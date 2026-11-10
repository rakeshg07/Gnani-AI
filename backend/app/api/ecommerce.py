"""API router for E-Commerce catalog, cart, orders, and returns backed by MongoDB."""
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.core.security import get_authenticated_customer
from app.schemas.ecommerce import (
    CategoryOut,
    ProductOut,
    ProductListResponse,
    CartOut,
    CartItemIn,
    CartItemUpdate,
    CheckoutIn,
    OrderOut,
    OrderListResponse,
    CancelOrderIn,
    ReturnRequestIn,
    ReturnRequestOut,
)
from app.services.ecommerce_service import ECommerceService, ECommerceException

router = APIRouter(tags=["E-Commerce"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Any = Depends(get_db)):
    """List all available product categories."""
    return ECommerceService.get_categories(db)


@router.get("/products", response_model=ProductListResponse)
def list_products(
    category_id: Optional[str] = Query(None, description="Filter by category slug or ID"),
    search: Optional[str] = Query(None, description="Keyword search in title and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Optional[str] = Query("featured", description="Sorting: featured, price_asc, price_desc, rating, newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Any = Depends(get_db),
):
    """Retrieve catalog products with full-text search, filtering, and sorting."""
    items, total = ECommerceService.get_products(
        db=db,
        category_id=category_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": [ProductOut.model_validate(p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product_details(product_id: str, db: Any = Depends(get_db)):
    """Retrieve complete specifications and details for a product by ID or slug."""
    product = ECommerceService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return ProductOut.model_validate(product)


@router.get("/cart", response_model=CartOut)
def view_cart(
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """View active shopping cart with live subtotal, tax, and item count."""
    cart = ECommerceService.get_cart(db, customer_id)
    return {
        "id": cart["id"],
        "customer_id": cart["customer_id"],
        "items": [
            {
                "id": it["id"],
                "product_id": it["product_id"],
                "product": ProductOut.model_validate(it["product"]),
                "quantity": it["quantity"],
                "unit_price": it["unit_price"],
                "total_price": it["total_price"],
            }
            for it in cart["items"]
        ],
        "subtotal": cart["subtotal"],
        "shipping_fee": cart["shipping_fee"],
        "tax_amount": cart["tax_amount"],
        "total_amount": cart["total_amount"],
        "item_count": cart["item_count"],
    }


@router.post("/cart/items", response_model=CartOut)
def add_item_to_cart(
    payload: CartItemIn,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Add a product with quantity to the active customer cart."""
    try:
        cart = ECommerceService.add_to_cart(
            db=db,
            customer_id=customer_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        return {
            "id": cart["id"],
            "customer_id": cart["customer_id"],
            "items": [
                {
                    "id": it["id"],
                    "product_id": it["product_id"],
                    "product": ProductOut.model_validate(it["product"]),
                    "quantity": it["quantity"],
                    "unit_price": it["unit_price"],
                    "total_price": it["total_price"],
                }
                for it in cart["items"]
            ],
            "subtotal": cart["subtotal"],
            "shipping_fee": cart["shipping_fee"],
            "tax_amount": cart["tax_amount"],
            "total_amount": cart["total_amount"],
            "item_count": cart["item_count"],
        }
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/cart/items/{product_id}", response_model=CartOut)
def update_cart_item_quantity(
    product_id: str,
    payload: CartItemUpdate,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Update quantity of an item in the cart. Set to 0 to remove."""
    try:
        cart = ECommerceService.update_cart_item(
            db=db,
            customer_id=customer_id,
            product_id=product_id,
            quantity=payload.quantity,
        )
        return {
            "id": cart["id"],
            "customer_id": cart["customer_id"],
            "items": [
                {
                    "id": it["id"],
                    "product_id": it["product_id"],
                    "product": ProductOut.model_validate(it["product"]),
                    "quantity": it["quantity"],
                    "unit_price": it["unit_price"],
                    "total_price": it["total_price"],
                }
                for it in cart["items"]
            ],
            "subtotal": cart["subtotal"],
            "shipping_fee": cart["shipping_fee"],
            "tax_amount": cart["tax_amount"],
            "total_amount": cart["total_amount"],
            "item_count": cart["item_count"],
        }
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/cart/items/{product_id}", response_model=CartOut)
def delete_cart_item(
    product_id: str,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Remove a product from the cart completely."""
    try:
        cart = ECommerceService.remove_cart_item(
            db=db,
            customer_id=customer_id,
            product_id=product_id,
        )
        return {
            "id": cart["id"],
            "customer_id": cart["customer_id"],
            "items": [
                {
                    "id": it["id"],
                    "product_id": it["product_id"],
                    "product": ProductOut.model_validate(it["product"]),
                    "quantity": it["quantity"],
                    "unit_price": it["unit_price"],
                    "total_price": it["total_price"],
                }
                for it in cart["items"]
            ],
            "subtotal": cart["subtotal"],
            "shipping_fee": cart["shipping_fee"],
            "tax_amount": cart["tax_amount"],
            "total_amount": cart["total_amount"],
            "item_count": cart["item_count"],
        }
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/checkout", response_model=OrderOut)
def checkout(payload: CheckoutIn, db: Any = Depends(get_db)):
    """Convert active cart into a confirmed order with simulated payment."""
    try:
        addr = payload.shipping_address.model_dump() if payload.shipping_address else None
        order = ECommerceService.checkout(
            db=db,
            customer_id=payload.customer_id or "cust_demo_001",
            shipping_address=addr,
            payment_method=payload.payment_method,
        )
        return OrderOut.model_validate(order)
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    status: Optional[str] = Query(None, description="Filter: processing, shipped, delivered, cancelled"),
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Retrieve all past orders for the customer."""
    orders = ECommerceService.get_orders(
        db=db,
        customer_id=customer_id,
        status_filter=status,
    )
    return {
        "items": [OrderOut.model_validate(o) for o in orders],
        "total": len(orders),
    }


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order_tracking(
    order_id: str,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Get live tracking status and milestone history for an order."""
    try:
        order = ECommerceService.get_order_by_id(
            db=db,
            order_id=order_id,
            customer_id=customer_id,
        )
        return OrderOut.model_validate(order)
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order_endpoint(
    order_id: str,
    payload: CancelOrderIn,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """Cancel an active order before delivery and initiate refund."""
    try:
        order = ECommerceService.cancel_order(
            db=db,
            order_id=order_id,
            customer_id=customer_id,
            reason=payload.reason,
        )
        return OrderOut.model_validate(order)
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/orders/{order_id}/returns", response_model=ReturnRequestOut)
def request_order_return_endpoint(
    order_id: str,
    payload: ReturnRequestIn,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """File a return request for a delivered item within the return window."""
    try:
        ret = ECommerceService.request_return(
            db=db,
            order_id=order_id,
            customer_id=customer_id,
            reason=payload.reason,
        )
        return ReturnRequestOut.model_validate(ret)
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/actions/confirm")
def confirm_pending_action_endpoint(
    token: str = Query(..., description="Confirmation token for consequential action"),
    confirmed: bool = Query(True, description="Whether customer confirmed or cancelled"),
    db: Any = Depends(get_db),
):
    """Confirm or reject a pending consequential action (order cancellation or return)."""
    try:
        result = ECommerceService.execute_pending_action(
            db=db,
            confirmation_token=token,
            confirmed=confirmed,
        )
        return result
    except ECommerceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
