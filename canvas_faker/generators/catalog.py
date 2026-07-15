"""Generator for catalog namespace."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from ..config import GenerationConfig
from ..ids import IdAllocator, Registry, new_uuid
from ..messiness import MessinessEngine

UTC = timezone.utc


def _dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(
    cfg: GenerationConfig,
    fake: Faker,
    ids: IdAllocator,
    reg: Registry,
    mess: MessinessEngine,
) -> dict[str, list[dict]]:
    rng = mess.rng
    now = datetime(2025, 8, 1, tzinfo=UTC)

    rows: dict[str, list[dict]] = {
        "accounts": [], "users": [], "products": [], "orders": [], "order_items": [],
        "payments": [], "enrollments": [], "certificates": [], "tags": [],
        "product_tags": [], "carts": [], "cart_items": [], "categories": [],
        "promotions": [], "bulk_checkouts": [], "bulk_invitations": [],
        "bulk_checkout_promotions": [], "cart_item_promotions": [],
        "order_item_promotions": [], "applicants": [], "account_admins": [],
        "themes": [], "email_layouts": [], "custom_emails": [],
        "certificate_templates": [], "user_defined_fields": [], "product_images": [],
        "program_requirements": [],
    }

    # Catalog accounts
    acct_ids = []
    for n in range(max(2, cfg.n_root_accounts)):
        aid = ids.next("catalog_accounts")
        created = _dt(now - timedelta(days=rng.randint(200, 600)))
        rows["accounts"].append({
            "id": aid, "created_at": created, "updated_at": created,
            "deleted_at": None, "name": f"Institution {n+1}",
            "parent_account_id": None, "canvas_account_id": None, "subdomain": f"inst{n+1}",
            "theme_id": None, "contact_email": fake.company_email(),
            "time_zone": fake.timezone(), "locale": "en", "visibility": "public",
            "active": True, "listing_count": 0, "root_account": True,
            "terms_of_service": None, "privacy_policy": None,
            "support_url": None, "support_email": fake.company_email(),
            "default_currency": "USD", "tax_rate": 0.0, "enabled": True,
            "canvas_domain": None, "custom_css": None,
        })
        acct_ids.append(aid)
        reg.register("catalog.accounts", aid)

    # Catalog users
    cat_user_ids = []
    for n in range(max(5, cfg.n_courses)):
        uid = ids.next("catalog_users")
        created = _dt(now - timedelta(days=rng.randint(100, 400)))
        rows["users"].append({
            "id": uid, "created_at": created, "updated_at": created,
            "deleted_at": None, "canvas_user_id": rng.randint(1, 100000),
            "name": fake.name(), "email": fake.email(),
            "time_zone": fake.timezone(), "locale": "en",
            "last_login_at": _dt(now - timedelta(days=rng.randint(1, 30))),
        })
        cat_user_ids.append(uid)
        reg.register("catalog.users", uid)

    # Products
    prod_ids = []
    for n in range(max(10, cfg.n_courses * 2)):
        pid = ids.next("catalog_products")
        created = _dt(now - timedelta(days=rng.randint(50, 300)))
        price = round(rng.uniform(49, 499), 2)
        rows["products"].append({
            "id": pid, "created_at": created, "updated_at": created,
            "deleted_at": None, "account_id": rng.choice(acct_ids),
            "canvas_course_id": None, "name": f"Course {n+1}: {fake.sentence(nb_words=3)}",
            "description": fake.paragraph(), "type": "Course", "visibility": "public",
            "listing_state": "active", "price": price, "currency": "USD",
            "seat_count": rng.randint(20, 500), "waitlist": rng.random() < 0.2,
            "enrollment_open_at": _dt(now - timedelta(days=30)),
            "enrollment_close_at": _dt(now + timedelta(days=60)),
            "starts_at": _dt(now), "ends_at": _dt(now + timedelta(days=180)),
            "duration": "12 weeks", "position": n, "featured": n < 3,
            "requires_application": False, "external_id": None, "sku": f"SKU{pid}",
            "cover_image_url": None, "thumbnail_url": None, "slug": f"course-{n+1}",
            "keywords": None, "credits": rng.choice([0.5, 1.0, 1.5, 2.0, 3.0, 4.0]),
            "level": rng.choice(["Beginner", "Intermediate", "Advanced"]),
            "language": "en", "instructor_name": fake.name(),
            "canvas_account_id": None, "root_program": False, "program": False,
            "certificate_enabled": rng.random() < 0.5,
        })
        prod_ids.append(pid)
        reg.register("catalog.products", pid)

    # Tags
    tag_ids = []
    for tag_name in ["Python", "Data Science", "Web Development", "Business", "Leadership"]:
        tid = ids.next("catalog_tags")
        rows["tags"].append({
            "id": tid, "created_at": _dt(now - timedelta(days=200)),
            "updated_at": _dt(now - timedelta(days=200)), "account_id": rng.choice(acct_ids),
            "name": tag_name,
        })
        tag_ids.append(tid)
        reg.register("catalog.tags", tid)

    # Product tags
    for pid in prod_ids:
        for _ in range(rng.randint(0, 3)):
            rows["product_tags"].append({
                "id": ids.next("catalog_product_tags"),
                "created_at": _dt(now - timedelta(days=100)),
                "product_id": pid, "tag_id": rng.choice(tag_ids),
            })

    # Orders + order items + payments
    for uid in cat_user_ids[:min(len(cat_user_ids), cfg.n_courses)]:
        oid = ids.next("catalog_orders")
        order_created = _dt(now - timedelta(days=rng.randint(1, 60)))
        n_items = rng.randint(1, 3)
        subtotal = 0.0
        rows["orders"].append({
            "id": oid, "created_at": order_created, "updated_at": order_created,
            "deleted_at": None, "user_id": uid, "status": rng.choice(["completed", "pending", "cancelled"]),
            "subtotal": None, "tax": 0.0, "total": None, "currency": "USD", "external_id": None,
        })
        reg.register("catalog.orders", oid)

        for _ in range(n_items):
            pid = rng.choice(prod_ids)
            qty = rng.randint(1, 3)
            price = rng.uniform(49, 499)
            item_total = price * qty
            subtotal += item_total
            rows["order_items"].append({
                "id": ids.next("catalog_order_items"), "created_at": order_created,
                "updated_at": order_created, "order_id": oid, "product_id": pid,
                "quantity": qty, "unit_price": price, "subtotal": item_total,
                "total": item_total,
            })

        # Update order totals
        for order in rows["orders"]:
            if order["id"] == oid:
                order["subtotal"] = subtotal
                order["total"] = subtotal

        # Payment
        rows["payments"].append({
            "id": ids.next("catalog_payments"), "created_at": order_created,
            "updated_at": order_created, "deleted_at": None, "order_id": oid,
            "amount": subtotal, "status": "completed", "gateway": "stripe",
        })

        # Enrollments
        for item_row in rows["order_items"]:
            if item_row["order_id"] == oid:
                eid = ids.next("catalog_enrollments")
                rows["enrollments"].append({
                    "id": eid, "created_at": order_created, "updated_at": order_created,
                    "deleted_at": None, "canvas_user_id": rng.randint(1, 100000),
                    "product_id": item_row["product_id"], "root_program_id": None,
                    "order_item_id": item_row["id"],
                    "requirements_completed_at": None,
                    "ends_at": _dt(now + timedelta(days=180)),
                    "external_id": None, "status": "active",
                    "last_sync_error": None,
                })
                reg.register("catalog.enrollments", eid)

    # Carts
    for uid in cat_user_ids[:min(len(cat_user_ids), max(3, cfg.n_courses // 5))]:
        cid = ids.next("catalog_carts")
        created = _dt(now - timedelta(days=rng.randint(0, 7)))
        rows["carts"].append({
            "id": cid, "created_at": created, "updated_at": created,
            "deleted_at": None, "user_id": uid, "status": "active",
            "subtotal": None, "total": None,
        })
        reg.register("catalog.carts", cid)

        cart_total = 0.0
        for _ in range(rng.randint(1, 2)):
            pid = rng.choice(prod_ids)
            price = rng.uniform(49, 499)
            cart_total += price
            rows["cart_items"].append({
                "id": ids.next("catalog_cart_items"), "created_at": created,
                "updated_at": created, "cart_id": cid, "product_id": pid,
            })

        for cart in rows["carts"]:
            if cart["id"] == cid:
                cart["subtotal"] = cart_total
                cart["total"] = cart_total

    # Promotions
    promo_ids = []
    for n in range(3):
        pid = ids.next("catalog_promotions")
        created = _dt(now - timedelta(days=100))
        rows["promotions"].append({
            "id": pid, "created_at": created, "updated_at": created,
            "deleted_at": None, "account_id": rng.choice(acct_ids),
            "name": f"Promo {n+1}", "code": f"PROMO{n+1}",
            "kind": rng.choice(["fixed", "percentage"]),
            "amount": rng.uniform(5, 50) if rng.random() < 0.5 else None,
            "percent": rng.uniform(5, 30) if rng.random() < 0.5 else None,
            "starts_at": _dt(now - timedelta(days=30)),
            "ends_at": _dt(now + timedelta(days=30)),
            "usage_limit": rng.randint(100, 1000),
            "used_count": rng.randint(0, 50),
        })
        promo_ids.append(pid)
        reg.register("catalog.promotions", pid)

    # Certificates
    cert_ids = []
    for _ in range(max(2, cfg.n_courses // 3)):
        cert_id = ids.next("catalog_certificates")
        created = _dt(now - timedelta(days=200))
        rows["certificates"].append({
            "id": cert_id, "created_at": created, "updated_at": created,
            "deleted_at": None, "product_id": rng.choice(prod_ids),
            "name": "Completion Certificate",
            "certificate_template_id": None, "custom_template_id": None,
            "active": True, "days_to_expire": None, "expires_at": None,
            "old_template": None, "old_pdf_settings": None,
        })
        cert_ids.append(cert_id)

    # Themes
    rows["themes"].append({
        "id": ids.next("catalog_themes"), "created_at": _dt(now - timedelta(days=300)),
        "updated_at": _dt(now - timedelta(days=300)), "deleted_at": None,
        "account_id": rng.choice(acct_ids), "name": "Default Theme",
        "primary_color": "#0066CC", "secondary_color": "#FFFFFF",
        "font": "Arial", "logo_url": None, "favicon_url": None,
        "custom_css": None, "custom_js": None, "active": True, "header_html": None,
    })

    # Email layouts
    layout_ids = []
    for name in ["Default", "Minimal"]:
        lid = ids.next("catalog_email_layouts")
        rows["email_layouts"].append({
            "id": lid, "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)), "account_id": rng.choice(acct_ids),
            "name": name,
        })
        layout_ids.append(lid)

    # Custom emails
    for _ in range(3):
        rows["custom_emails"].append({
            "id": ids.next("catalog_custom_emails"),
            "created_at": _dt(now - timedelta(days=100)),
            "updated_at": _dt(now - timedelta(days=100)), "deleted_at": None,
            "account_id": rng.choice(acct_ids),
            "name": f"Email {rng.randint(1,5)}", "subject": fake.sentence(),
            "body": fake.paragraph(), "email_layout_id": rng.choice(layout_ids) if layout_ids else None,
            "active": True, "kind": "confirmation",
        })

    # Categories
    for n in range(3):
        rows["categories"].append({
            "id": ids.next("catalog_categories"),
            "created_at": _dt(now - timedelta(days=250)),
            "updated_at": _dt(now - timedelta(days=250)), "account_id": rng.choice(acct_ids),
            "name": f"Category {n+1}", "position": n,
        })

    # Account admins
    for uid in cat_user_ids[:min(len(cat_user_ids), max(2, cfg.n_root_accounts))]:
        rows["account_admins"].append({
            "id": ids.next("catalog_account_admins"),
            "created_at": _dt(now - timedelta(days=300)),
            "updated_at": _dt(now - timedelta(days=300)), "deleted_at": None,
            "account_id": rng.choice(acct_ids), "canvas_user_id": rng.randint(1, 100000),
            "role": "admin", "active": True,
        })

    # Bulk checkout
    if cat_user_ids and prod_ids:
        bc_id = ids.next("catalog_bulk_checkouts")
        created = _dt(now - timedelta(days=20))
        rows["bulk_checkouts"].append({
            "id": bc_id, "created_at": created, "updated_at": created,
            "deleted_at": None, "user_id": rng.choice(cat_user_ids),
            "status": "completed", "total": rng.uniform(500, 5000), "seats": rng.randint(10, 50),
        })

        for _ in range(rng.randint(1, 3)):
            rows["bulk_invitations"].append({
                "id": ids.next("catalog_bulk_invitations"),
                "created_at": created, "updated_at": created, "deleted_at": None,
                "bulk_checkout_id": bc_id, "email": fake.email(),
                "status": "sent", "sent_at": created, "redeemed_at": None,
                "token": new_uuid()[:16],
            })

    return rows
