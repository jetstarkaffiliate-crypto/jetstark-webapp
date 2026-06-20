import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.core.dependencies import get_current_user, require_role, get_optional_user
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    search: str = Query(None),
    sort: str = Query("popular"),
    user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.status == ProductStatus.PUBLISHED)

    if category:
        query = query.where(Product.category == category)
    if search:
        query = query.where(
            or_(
                Product.title.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    match sort:
        case "newest":
            query = query.order_by(Product.created_at.desc())
        case "price-low":
            query = query.order_by(Product.price.asc())
        case "price-high":
            query = query.order_by(Product.price.desc())
        case "rating":
            query = query.order_by(Product.rating.desc())
        case _:
            query = query.order_by(Product.sales_count.desc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()

    product_responses = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.vendor_name = p.vendor.full_name if p.vendor else None
        product_responses.append(resp)

    return ProductListResponse(products=product_responses, total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=list[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product.category).where(Product.status == ProductStatus.PUBLISHED).distinct().order_by(Product.category))
    cats = [r[0] for r in result.all()]
    return cats


@router.get("/my-products", response_model=list[ProductResponse])
async def get_vendor_products(
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.vendor_id == current_user.id).order_by(Product.created_at.desc())
    )
    products = result.scalars().all()
    responses = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.vendor_name = current_user.full_name
        responses.append(resp)
    return responses


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    resp = ProductResponse.model_validate(product)
    resp.vendor_name = product.vendor.full_name if product.vendor else None
    return resp


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    product = Product(
        vendor_id=current_user.id,
        title=data.title,
        description=data.description,
        category=data.category,
        price=data.price,
        commission_rate=data.commission_rate,
        cover_image_url=data.cover_image_url,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    resp = ProductResponse.model_validate(product)
    resp.vendor_name = current_user.full_name
    return resp


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.vendor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    resp = ProductResponse.model_validate(product)
    resp.vendor_name = current_user.full_name
    return resp


@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.VENDOR)),
):
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")) / "products"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    path = UPLOAD_DIR / filename
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/products/{filename}"}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.vendor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")

    await db.delete(product)
    await db.commit()


@router.get("/admin/all", response_model=list[ProductResponse])
async def list_all_products_admin(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(
        select(Product).order_by(Product.created_at.desc())
    )
    products = result.scalars().all()
    responses = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.vendor_name = p.vendor.full_name if p.vendor else None
        responses.append(resp)
    return responses


@router.get("/admin/pending", response_model=list[ProductResponse])
async def list_pending_products(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(
        select(Product).where(Product.status == ProductStatus.PENDING).order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    responses = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.vendor_name = p.vendor.full_name if p.vendor else None
        responses.append(resp)
    return responses


@router.post("/admin/{product_id}/approve")
async def approve_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.status = ProductStatus.PUBLISHED
    await db.commit()
    return {"message": "Product approved"}


@router.post("/admin/{product_id}/reject")
async def reject_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.status = ProductStatus.REJECTED
    await db.commit()
    return {"message": "Product rejected"}
