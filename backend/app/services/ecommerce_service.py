"""Business logic service for VoiceIQ India E-Commerce operations backed by MongoDB."""
import random
import string
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pymongo import ASCENDING, DESCENDING

from app.core.logging import logger
from app.core.security import generate_secure_token


class ECommerceException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "ECOMMERCE_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_order_id() -> str:
    digits = "".join(random.choices(string.digits, k=5))
    return f"VIQ-{digits}"


def generate_tracking_number(carrier: str) -> str:
    prefix = "DEL" if "Delhivery" in carrier else ("BLU" if "Blue" in carrier else "EKP")
    digits = "".join(random.choices(string.digits, k=8))
    return f"{prefix}{digits}IN"


class ECommerceService:
    _SEARCH_STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "can", "could", "would", "should", "will", "do", "does", "did", "have", "has", "had",
        "i", "me", "my", "we", "you", "your", "it", "its", "this", "that", "these", "those",
        "in", "on", "at", "for", "to", "of", "with", "from", "by", "about", "into", "or", "and",
        "what", "which", "who", "where", "when", "how", "any", "all", "some", "every",
        "search", "find", "show", "list", "out", "get", "give", "tell", "look", "looking",
        "want", "need", "browse", "check", "please", "pls", "available", "availability",
        "stock", "brand", "brands", "item", "items", "product", "products", "price",
        "under", "below", "less", "than", "above", "over", "between", "rs", "inr", "rupees",
        "dikhao", "dhoondo", "chahiye", "batao", "hai", "kya", "ka", "ke", "ki", "ko", "mein",
    }

    _SEARCH_SYNONYMS: Dict[str, List[str]] = {
        "mobile": ["oneplus", "nord", "5g", "snapdragon", "smartphone", "phone"],
        "mobiles": ["oneplus", "nord", "5g", "snapdragon", "smartphone", "phone"],
        "smartphone": ["oneplus", "nord", "5g", "snapdragon", "mobile", "phone"],
        "smartphones": ["oneplus", "nord", "5g", "snapdragon", "mobile", "phone"],
        "phone": ["oneplus", "nord", "5g", "snapdragon", "smartphone", "mobile"],
        "phones": ["oneplus", "nord", "5g", "snapdragon", "smartphone", "mobile"],
        "earbud": ["earbuds", "boat", "nirvana"],
        "earbuds": ["earbuds", "boat", "nirvana"],
        "earphone": ["earbuds", "headphones", "boat", "sony"],
        "earphones": ["earbuds", "headphones", "boat", "sony"],
        "tws": ["earbuds", "boat", "nirvana"],
        "headphone": ["headphones", "sony", "wh-1000xm4"],
        "headphones": ["headphones", "sony", "wh-1000xm4"],
        "headset": ["headphones", "earbuds", "sony", "boat"],
        "audio": ["earbuds", "headphones", "boat", "sony"],
        "watch": ["watch", "smartwatch", "titan", "colorfit", "chronograph"],
        "watches": ["watch", "smartwatch", "titan", "colorfit", "chronograph"],
        "smartwatch": ["smartwatch", "colorfit"],
        "smartwatches": ["smartwatch", "colorfit"],
        "bag": ["backpack", "tourister", "american"],
        "bags": ["backpack", "tourister", "american"],
        "backpack": ["backpack", "tourister", "american"],
        "backpacks": ["backpack", "tourister", "american"],
        "shirt": ["shirt", "linen", "louis", "philippe"],
        "shirts": ["shirt", "linen", "louis", "philippe"],
        "kurti": ["kurti", "festive", "silk", "woman", "dupatta"],
        "kurtis": ["kurti", "festive", "silk", "woman", "dupatta"],
        "kurta": ["kurti", "festive", "silk", "woman"],
        "clothes": ["kurti", "shirt", "fashion", "linen", "silk"],
        "apparel": ["kurti", "shirt", "fashion", "linen", "silk"],
        "mixer": ["mixer", "grinder", "preethi", "zodiac"],
        "grinder": ["mixer", "grinder", "preethi", "zodiac"],
        "mixie": ["mixer", "grinder", "preethi"],
        "fryer": ["fryer", "philips"],
        "airfryer": ["fryer", "philips"],
        "fan": ["fan", "havells", "bldc", "ceiling"],
        "fans": ["fan", "havells", "bldc", "ceiling"],
        "kitchen": ["mixer", "grinder", "fryer", "preethi", "philips", "appliances"],
        "appliance": ["mixer", "grinder", "fryer", "fan", "preethi", "philips", "havells"],
        "appliances": ["mixer", "grinder", "fryer", "fan", "preethi", "philips", "havells"],
        "electronics": ["oneplus", "boat", "sony", "colorfit", "earbuds", "headphones", "smartwatch"],
        "gadget": ["oneplus", "boat", "sony", "colorfit", "earbuds", "headphones", "smartwatch"],
        "gadgets": ["oneplus", "boat", "sony", "colorfit", "earbuds", "headphones", "smartwatch"],
    }

    @classmethod
    def _extract_search_terms(cls, search: str) -> Tuple[List[str], List[str]]:
        """Extracts meaningful keywords and expanded synonyms from a natural-language query."""
        # Remove price phrases like "under 2000" or "₹2000"
        cleaned = re.sub(r"(?:under|below|less than|within|upto)\s*(?:rs\.?|inr|₹)?\s*[0-9,]+", " ", search, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?:rs\.?|inr|₹)\s*[0-9,]+", " ", cleaned, flags=re.IGNORECASE)
        raw_tokens = re.findall(r"[a-z0-9\-]+", cleaned.lower())

        primary_tokens: List[str] = []
        for tok in raw_tokens:
            if tok in cls._SEARCH_STOP_WORDS or len(tok) <= 1:
                continue
            if tok not in primary_tokens:
                primary_tokens.append(tok)

        expanded_tokens: List[str] = list(primary_tokens)
        for tok in primary_tokens:
            for syn in cls._SEARCH_SYNONYMS.get(tok, []):
                if syn not in expanded_tokens:
                    expanded_tokens.append(syn)
            # Also add simple singular form if ending in 's'
            if len(tok) > 3 and tok.endswith("s"):
                singular = tok[:-1]
                if singular not in expanded_tokens:
                    expanded_tokens.append(singular)
                for syn in cls._SEARCH_SYNONYMS.get(singular, []):
                    if syn not in expanded_tokens:
                        expanded_tokens.append(syn)

        return primary_tokens, expanded_tokens

    @staticmethod
    def get_categories(db: Any) -> List[Dict[str, Any]]:
        categories = list(db.categories.find().sort("name", ASCENDING))
        for c in categories:
            c["id"] = c.get("id") or str(c.get("_id", ""))
        return categories

    @staticmethod
    def get_products(
        db: Any,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: Optional[str] = "featured",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        filters: Dict[str, Any] = {}

        if category_id and category_id.lower() != "all":
            filters["category_id"] = category_id

        price_filters: Dict[str, Any] = {}
        if min_price is not None:
            price_filters["$gte"] = float(min_price)
        if max_price is not None:
            price_filters["$lte"] = float(max_price)
        if price_filters:
            filters["price"] = price_filters

        # Sorting
        sort_field = [("is_featured", DESCENDING), ("rating", DESCENDING)]
        if sort_by == "price_asc":
            sort_field = [("price", ASCENDING)]
        elif sort_by == "price_desc":
            sort_field = [("price", DESCENDING)]
        elif sort_by == "rating":
            sort_field = [("rating", DESCENDING)]
        elif sort_by == "newest":
            sort_field = [("created_at", DESCENDING)]

        if search and search.strip():
            primary_tokens, expanded_tokens = ECommerceService._extract_search_terms(search)
            if expanded_tokens:
                # Score candidates matching price + category filters
                candidates = list(db.products.find(filters).sort(sort_field))
                scored: List[Tuple[int, Dict[str, Any]]] = []
                for p in candidates:
                    specs_str = " ".join(f"{k} {v}" for k, v in (p.get("specifications") or {}).items())
                    haystack_title = f"{p.get('title', '')} {p.get('slug', '')} {p.get('badge', '')}".lower()
                    haystack_body = f"{p.get('description', '')} {p.get('category_id', '')} {specs_str}".lower()

                    score = 0
                    for tok in primary_tokens:
                        pat = re.compile(rf"\b{re.escape(tok)}\b")
                        if pat.search(haystack_title):
                            score += 10
                        elif pat.search(haystack_body):
                            score += 5
                    for tok in expanded_tokens:
                        if tok not in primary_tokens:
                            pat = re.compile(rf"\b{re.escape(tok)}\b")
                            if pat.search(haystack_title):
                                score += 4
                            elif pat.search(haystack_body):
                                score += 2

                    if score > 0:
                        scored.append((score, p))

                scored.sort(key=lambda pair: (pair[0], float(pair[1].get("rating", 0))), reverse=True)
                matched = [pair[1] for pair in scored]
                total = len(matched)
                skip = (page - 1) * page_size
                items = matched[skip : skip + page_size]
                for p in items:
                    p["id"] = p.get("id") or str(p.get("_id", ""))
                    if "created_at" not in p or not p["created_at"]:
                        p["created_at"] = get_utc_now()
                return items, total

        total = db.products.count_documents(filters)
        skip = (page - 1) * page_size
        items = list(db.products.find(filters).sort(sort_field).skip(skip).limit(page_size))

        for p in items:
            p["id"] = p.get("id") or str(p.get("_id", ""))
            if "created_at" not in p or not p["created_at"]:
                p["created_at"] = get_utc_now()

        return items, total

    @staticmethod
    def get_product_by_id(db: Any, product_id: str) -> Optional[Dict[str, Any]]:
        p = db.products.find_one({"$or": [{"id": product_id}, {"_id": product_id}, {"slug": product_id}]})
        if p:
            p["id"] = p.get("id") or str(p.get("_id", ""))
            if "created_at" not in p or not p["created_at"]:
                p["created_at"] = get_utc_now()
        return p

    @staticmethod
    def get_cart(db: Any, customer_id: str) -> Dict[str, Any]:
        cart = db.carts.find_one({"customer_id": customer_id})
        if not cart:
            cart = {
                "_id": f"cart_{customer_id}",
                "id": f"cart_{customer_id}",
                "customer_id": customer_id,
                "created_at": get_utc_now(),
                "updated_at": get_utc_now(),
                "items": [],
            }
            db.carts.insert_one(cart)

        cart_id = cart.get("id") or str(cart.get("_id", ""))
        raw_items = cart.get("items", [])
        formatted_items = []
        subtotal = 0.0

        for item in raw_items:
            prod = ECommerceService.get_product_by_id(db, item.get("product_id", ""))
            if not prod:
                continue
            unit_price = float(prod.get("price", 0.0))
            qty = int(item.get("quantity", 1))
            total_price = round(unit_price * qty, 2)
            subtotal += total_price

            formatted_items.append({
                "id": item.get("id", str(uuid.uuid4())),
                "product_id": prod["id"],
                "product": prod,
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total_price,
            })

        subtotal = round(subtotal, 2)
        shipping_fee = 0.0 if (subtotal >= 499.0 or subtotal == 0) else 49.0
        tax_amount = round(subtotal * 0.05, 2) if subtotal > 0 else 0.0
        total_amount = round(subtotal + shipping_fee + tax_amount, 2)
        item_count = sum(i["quantity"] for i in formatted_items)

        return {
            "id": cart_id,
            "customer_id": customer_id,
            "items": formatted_items,
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "item_count": item_count,
        }

    @staticmethod
    def add_to_cart(db: Any, customer_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        prod = ECommerceService.get_product_by_id(db, product_id)
        if not prod:
            raise ECommerceException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

        cart = db.carts.find_one({"customer_id": customer_id})
        items = cart.get("items", []) if cart else []
        found = False

        for it in items:
            if it.get("product_id") == prod["id"]:
                it["quantity"] = it.get("quantity", 0) + quantity
                it["unit_price"] = prod["price"]
                found = True
                break

        if not found:
            items.append({
                "id": f"item_{uuid.uuid4().hex[:8]}",
                "product_id": prod["id"],
                "quantity": quantity,
                "unit_price": prod["price"],
            })

        db.carts.update_one(
            {"customer_id": customer_id},
            {
                "$set": {
                    "items": items,
                    "updated_at": get_utc_now(),
                },
                "$setOnInsert": {
                    "_id": f"cart_{customer_id}",
                    "id": f"cart_{customer_id}",
                    "created_at": get_utc_now(),
                },
            },
            upsert=True,
        )
        return ECommerceService.get_cart(db, customer_id)

    @staticmethod
    def update_cart_item(db: Any, customer_id: str, product_id: str, quantity: int) -> Dict[str, Any]:
        if quantity <= 0:
            return ECommerceService.remove_cart_item(db, customer_id, product_id)

        cart = db.carts.find_one({"customer_id": customer_id})
        items = cart.get("items", []) if cart else []
        for it in items:
            if it.get("product_id") == product_id:
                it["quantity"] = quantity
                break

        db.carts.update_one(
            {"customer_id": customer_id},
            {"$set": {"items": items, "updated_at": get_utc_now()}},
        )
        return ECommerceService.get_cart(db, customer_id)

    @staticmethod
    def remove_cart_item(db: Any, customer_id: str, product_id: str) -> Dict[str, Any]:
        cart = db.carts.find_one({"customer_id": customer_id})
        items = cart.get("items", []) if cart else []
        filtered_items = [it for it in items if it.get("product_id") != product_id]

        db.carts.update_one(
            {"customer_id": customer_id},
            {"$set": {"items": filtered_items, "updated_at": get_utc_now()}},
        )
        return ECommerceService.get_cart(db, customer_id)

    @staticmethod
    def clear_cart(db: Any, customer_id: str) -> Dict[str, Any]:
        db.carts.update_one(
            {"customer_id": customer_id},
            {"$set": {"items": [], "updated_at": get_utc_now()}},
        )
        return ECommerceService.get_cart(db, customer_id)

    @staticmethod
    def checkout(
        db: Any,
        customer_id: str,
        shipping_address: Optional[Dict[str, Any]] = None,
        payment_method: str = "UPI (Simulated)",
    ) -> Dict[str, Any]:
        cart = ECommerceService.get_cart(db, customer_id)
        if not cart["items"]:
            raise ECommerceException("Cart is empty", status_code=400, code="CART_EMPTY")

        now = get_utc_now()
        order_id = generate_order_id()
        carrier = "Delhivery Express"
        tracking_num = generate_tracking_number(carrier)

        # Fallback shipping address from customer profile if not provided
        if not shipping_address:
            cust = db.users.find_one({"id": customer_id}) or db.customers.find_one({"id": customer_id})
            if cust:
                shipping_address = {
                    "name": cust.get("name", "Valued Customer"),
                    "phone": cust.get("phone", "+91 98450 12345"),
                    "address_line": cust.get("address_line", "Main Street"),
                    "city": cust.get("city", "Bengaluru"),
                    "state": cust.get("state", "Karnataka"),
                    "postal_code": cust.get("postal_code", "560001"),
                }
            else:
                shipping_address = {
                    "name": "Aarav Sharma",
                    "phone": "+91 98450 12345",
                    "address_line": "Flat 402, Skyline Residency, 12th Main, Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "postal_code": "560038",
                }

        order_items = []
        for it in cart["items"]:
            prod = it["product"]
            order_items.append({
                "id": f"item_{uuid.uuid4().hex[:8]}",
                "order_id": order_id,
                "product_id": prod["id"],
                "product_title": prod["title"],
                "product_image": prod["image_url"],
                "unit_price": it["unit_price"],
                "quantity": it["quantity"],
                "total_price": it["total_price"],
            })

        order_doc = {
            "_id": order_id,
            "id": order_id,
            "customer_id": customer_id,
            "status": "processing",
            "subtotal": cart["subtotal"],
            "shipping_fee": cart["shipping_fee"],
            "tax_amount": cart["tax_amount"],
            "total_amount": cart["total_amount"],
            "payment_method": payment_method,
            "payment_status": "completed",
            "shipping_address": shipping_address,
            "tracking_number": tracking_num,
            "carrier": carrier,
            "expected_delivery": now + timedelta(days=3),
            "created_at": now,
            "tracking_events": [
                {
                    "status": "ordered",
                    "title": "Order Placed Successfully",
                    "timestamp": now.strftime("%Y-%m-%d %H:%M"),
                    "location": f"{shipping_address.get('city', 'Bengaluru')} Fulfillment Hub",
                    "description": f"Payment verified via {payment_method}. Seller preparing shipment.",
                }
            ],
            "items": order_items,
            "returns": [],
        }

        db.orders.insert_one(order_doc)
        ECommerceService.clear_cart(db, customer_id)
        return order_doc

    @staticmethod
    def get_orders(
        db: Any,
        customer_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"customer_id": customer_id}
        if status_filter and status_filter.lower() != "all":
            query["status"] = status_filter.lower()

        orders = list(db.orders.find(query).sort("created_at", DESCENDING).limit(limit))
        for o in orders:
            o["id"] = o.get("id") or str(o.get("_id", ""))
        return orders

    @staticmethod
    def get_order_by_id(db: Any, order_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        query: Dict[str, Any] = {"$or": [{"id": order_id}, {"_id": order_id}]}
        if customer_id:
            query["customer_id"] = customer_id

        order = db.orders.find_one(query)
        if not order:
            raise ECommerceException(f"Order #{order_id} not found", status_code=404, code="ORDER_NOT_FOUND")
        order["id"] = order.get("id") or str(order.get("_id", ""))
        return order

    @staticmethod
    def cancel_order(
        db: Any,
        order_id: str,
        customer_id: str,
        reason: Optional[str] = "Customer requested cancellation",
    ) -> Dict[str, Any]:
        order = ECommerceService.get_order_by_id(db, order_id, customer_id)
        current_status = order.get("status", "")

        if current_status == "delivered":
            raise ECommerceException(
                "Delivered orders cannot be cancelled. You can request a return instead.",
                status_code=400,
                code="CANNOT_CANCEL_DELIVERED",
            )
        if current_status == "cancelled":
            raise ECommerceException("Order is already cancelled.", status_code=400, code="ALREADY_CANCELLED")

        now = get_utc_now()
        events = order.get("tracking_events", [])
        events.append({
            "status": "cancelled",
            "title": "Order Cancelled",
            "timestamp": now.strftime("%Y-%m-%d %H:%M"),
            "location": "VoiceIQ Operations Hub",
            "description": f"Cancellation confirmed: {reason}. Refund initiated.",
        })

        db.orders.update_one(
            {"id": order["id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": now,
                    "cancellation_reason": reason,
                    "tracking_events": events,
                }
            },
        )
        return ECommerceService.get_order_by_id(db, order["id"], customer_id)

    @staticmethod
    def request_return(
        db: Any,
        order_id: str,
        customer_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        order = ECommerceService.get_order_by_id(db, order_id, customer_id)
        current_status = order.get("status", "")

        if current_status != "delivered":
            raise ECommerceException(
                f"Returns can only be requested for delivered orders. Current status: {current_status}",
                status_code=400,
                code="NOT_DELIVERED",
            )

        # Check existing return
        existing_return = db.return_requests.find_one({"order_id": order["id"]})
        if existing_return:
            raise ECommerceException(
                f"A return request #{existing_return.get('id')} already exists for order #{order['id']}.",
                status_code=400,
                code="RETURN_ALREADY_EXISTS",
            )

        now = get_utc_now()
        ret_id = f"RET-{random.randint(10000, 99999)}"
        ret_doc = {
            "_id": ret_id,
            "id": ret_id,
            "order_id": order["id"],
            "customer_id": customer_id,
            "reason": reason,
            "status": "requested",
            "refund_amount": order.get("total_amount", 0.0),
            "created_at": now,
            "resolution_notes": "Return request received via VoiceIQ. Courier pickup will be scheduled in 24 hours.",
        }

        db.return_requests.insert_one(ret_doc)

        # Update order events
        events = order.get("tracking_events", [])
        events.append({
            "status": "return_requested",
            "title": "Return Initiated",
            "timestamp": now.strftime("%Y-%m-%d %H:%M"),
            "location": "Doorstep Pickup Scheduled",
            "description": f"Return {ret_id} filed. Reason: {reason}.",
        })
        db.orders.update_one(
            {"id": order["id"]},
            {
                "$set": {"tracking_events": events},
                "$push": {"returns": ret_doc},
            },
        )
        return ret_doc

    @staticmethod
    def create_pending_action(
        db: Any,
        customer_id: str,
        action_type: str,
        order_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        order = ECommerceService.get_order_by_id(db, order_id, customer_id)
        token = generate_secure_token(24)
        now = get_utc_now()
        action_id = f"act_{uuid.uuid4().hex[:12]}"

        prompt = (
            f"Are you sure you want to cancel Order #{order['id']} for ₹{order.get('total_amount', 0):,.2f}?"
            if action_type == "cancel_order"
            else f"Confirm return request for Order #{order['id']} (Refund: ₹{order.get('total_amount', 0):,.2f})?"
        )

        pending_doc = {
            "_id": action_id,
            "id": action_id,
            "customer_id": customer_id,
            "action_type": action_type,
            "order_id": order["id"],
            "confirmation_token": token,
            "status": "pending",
            "details": details or {},
            "created_at": now,
            "expires_at": now + timedelta(minutes=15),
            "confirmation_prompt": prompt,
        }

        db.pending_actions.insert_one(pending_doc)
        return pending_doc

    @staticmethod
    def execute_pending_action(
        db: Any,
        confirmation_token: str,
        confirmed: bool,
    ) -> Dict[str, Any]:
        action = db.pending_actions.find_one({"confirmation_token": confirmation_token})
        if not action:
            raise ECommerceException("Invalid or unknown confirmation token.", status_code=404, code="TOKEN_NOT_FOUND")

        if action.get("status") != "pending":
            raise ECommerceException(f"This action has already been {action.get('status')}.", status_code=400, code="ACTION_ALREADY_PROCESSED")

        now = get_utc_now()
        expires_at = action.get("expires_at")
        if expires_at and expires_at.replace(tzinfo=timezone.utc) < now:
            db.pending_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "expired"}})
            raise ECommerceException("Confirmation window expired (15 minutes). Please initiate your request again.", status_code=400, code="ACTION_EXPIRED")

        if not confirmed:
            db.pending_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "cancelled"}})
            return {
                "success": False,
                "action": action.get("action_type"),
                "order_id": action.get("order_id"),
                "message": "Action cancelled as requested. Your order remains unchanged.",
            }

        action_type = action.get("action_type")
        order_id = action.get("order_id")
        customer_id = action.get("customer_id")
        details = action.get("details", {})

        if action_type == "cancel_order":
            order = ECommerceService.cancel_order(db, order_id, customer_id, details.get("reason", "Cancelled by customer via VoiceIQ"))
            db.pending_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "consumed", "consumed_at": now}})
            return {
                "success": True,
                "action": "cancel_order",
                "order_id": order_id,
                "order": order,
                "message": f"Order #{order_id} has been successfully cancelled. Refund of ₹{order.get('total_amount', 0):,.2f} initiated.",
            }
        elif action_type == "create_return":
            ret = ECommerceService.request_return(db, order_id, customer_id, details.get("reason", "Return requested via VoiceIQ"))
            db.pending_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "consumed", "consumed_at": now}})
            return {
                "success": True,
                "action": "create_return",
                "order_id": order_id,
                "return_request": ret,
                "message": f"Return request #{ret.get('id')} submitted successfully. Doorstep pickup will be scheduled within 24 hours.",
            }
        else:
            raise ECommerceException(f"Unsupported action type: {action_type}", status_code=400)

    @staticmethod
    def consume_pending_action(
        db: Any,
        confirmation_token: str,
        customer_id: str,
        action: Optional[str] = None,
        target_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Any]:
        act = db.pending_actions.find_one({"confirmation_token": confirmation_token})
        if not act:
            raise ECommerceException("Invalid or unknown confirmation token.", status_code=404, code="TOKEN_NOT_FOUND")
        if act.get("customer_id") != customer_id:
            raise ECommerceException("Confirmation token does not belong to active customer.", status_code=403, code="CUSTOMER_MISMATCH")

        res = ECommerceService.execute_pending_action(db, confirmation_token, confirmed=True)
        result_obj = res.get("order") or res.get("return_request") or {}
        return act, result_obj

    @staticmethod
    def get_store_analytics(db: Any) -> Dict[str, Any]:
        orders = list(db.orders.find())
        total_orders = len(orders)
        total_revenue = sum(o.get("total_amount", 0.0) for o in orders if o.get("status") != "cancelled")
        active_orders = sum(1 for o in orders if o.get("status") in ["processing", "shipped"])
        returns = db.return_requests.count_documents({})
        products = db.products.count_documents({})
        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "active_orders": active_orders,
            "total_returns": returns,
            "total_products": products,
        }


