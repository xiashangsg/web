#!/usr/bin/env python3
"""Embed static product cards into products.html from 产品目录.json (build-time only)."""
import html
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCTS_HTML = ROOT / "products.html"
CATALOG_JSON = ROOT / "产品目录.json"

WHATSAPP_NUMBER = "6585588100"
WA_TEMPLATE = "你好,我需要{productName}{model}.——来自XIASHANG官网的消息"
WHATSAPP_ICON = "https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg"

BRAND_PART_CATS = {
    "Drive Shaft / 传动轴",
    "Brake Pad / 刹车片",
    "Brake Drum / 制动鼓",
    "Link Rod / 拉杆",
    "Brake Shoe / 蹄铁",
}

CATEGORY_ZH = {
    "Bus Windscreen": "巴士玻璃",
    "Radiator": "水箱",
    "Drive Shaft": "传动轴",
    "Brake Pad": "刹车片",
    "Brake Drum": "制动鼓",
    "Link Rod": "拉杆",
    "Brake Shoe": "蹄铁",
}


def esc(text):
    return html.escape(str(text if text is not None else ""))


def split_product_name(name):
    s = str(name or "").strip()
    if not s:
        return "", ""
    has_cn = bool(re.search(r"[\u4e00-\u9fff]", s))
    has_en = bool(re.search(r"[A-Za-z]", s))
    if has_cn and has_en:
        m = re.search(r"[A-Za-z]", s)
        if m and m.start() > 0:
            return s[: m.start()].strip(), s[m.start() :].strip()
    if has_cn:
        return s, ""
    return "", s


def category_display_label(cat):
    cat = str(cat or "").strip()
    if not cat:
        return ""
    if " / " in cat:
        return cat
    zh = CATEGORY_ZH.get(cat)
    return f"{cat} / {zh}" if zh else cat


def parse_bilingual_category(cat):
    cat = str(cat or "").strip()
    if " / " in cat:
        en, zh = cat.split(" / ", 1)
        return en.strip(), zh.strip()
    return cat, CATEGORY_ZH.get(cat, "")


def is_show_true(val):
    v = str(val or "").strip().lower()
    return v in ("true", "yes", "1")


def apply_wa_template(product, is_brand):
    cat = product.get("category", "")
    pname = product.get("productName", "")
    display = product.get("displayText", "")
    if is_brand:
        cn, en = split_product_name(pname or display)
        brand_cn = cn or en
        _, cat_zh = parse_bilingual_category(cat)
        detail = f" {cat_zh}" if cat_zh else ""
        msg = WA_TEMPLATE.replace("{productName}", brand_cn).replace("{model}", detail)
    else:
        cn, en = split_product_name(pname)
        name_val = cn or en
        model_val = str(display or "").strip()
        model_part = f"  {model_val}" if model_val else ""
        msg = WA_TEMPLATE.replace("{productName}", name_val).replace("{model}", model_part)
    return (
        "https://api.whatsapp.com/send?phone="
        + urllib.parse.quote(WHATSAPP_NUMBER)
        + "&text="
        + urllib.parse.quote(msg)
    )


def format_product_name_html(name):
    cn, en = split_product_name(name)
    if cn and en:
        return (
            f'<span class="name-cn">{esc(cn)}</span>'
            f'<span class="name-en">{esc(en)}</span>'
        )
    if cn:
        return f'<span class="name-cn">{esc(cn)}</span>'
    if en:
        return f'<span class="name-en name-en-only">{esc(en)}</span>'
    return "-"


def format_inline_bilingual_html(text):
    cn, en = split_product_name(text)
    if cn and en:
        return (
            '<span class="name-inline">'
            f'<span class="name-cn-inline">{esc(cn)}</span> '
            f'<span class="name-en-inline">{esc(en)}</span>'
            "</span>"
        )
    if cn:
        return f'<span class="name-inline name-cn-inline">{esc(cn)}</span>'
    if en:
        return f'<span class="name-inline name-en-inline">{esc(en)}</span>'
    return "-"


def build_card(product):
    cat = product.get("category", "")
    pname = product.get("productName", "")
    display = product.get("displayText", "")
    keywords = product.get("searchKeywords", "")
    idx = product.get("index", "")
    is_brand = cat in BRAND_PART_CATS
    wa = apply_wa_template(product, is_brand)
    pill = esc(category_display_label(cat))

    attrs = (
        f'data-index="{esc(idx)}" '
        f'data-category="{esc(cat)}" '
        f'data-product-name="{esc(pname)}" '
        f'data-search-keywords="{esc(keywords)}" '
        f'data-display-text="{esc(display)}" '
        f'data-brand-part="{"true" if is_brand else "false"}"'
    )

    if is_brand:
        brand_text = display or pname
        body = (
            '<div class="body">'
            '<div class="card-text">'
            f'<span class="category-pill">{pill}</span>'
            '<div class="field field-model field-brand"><strong>'
            '<span class="field-label-cn">适用品牌</span> '
            '<span class="field-label-sep">/</span> '
            '<span class="field-label-en">Brand:</span></strong> '
            f'<span class="model-value model-value-inline">{format_inline_bilingual_html(brand_text)}</span>'
            "</div></div>"
            f'<a class="product-wa-round" href="{esc(wa)}" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp quote">'
            f'<img src="{WHATSAPP_ICON}" alt="">'
            "</a></div>"
        )
    else:
        body = (
            '<div class="body">'
            '<div class="card-text">'
            f'<span class="category-pill">{pill}</span>'
            f'<h2 class="name">{format_product_name_html(pname)}</h2>'
            '<div class="field field-model"><strong>'
            '<span class="field-label-cn">适用车型</span> '
            '<span class="field-label-sep">/</span> '
            '<span class="field-label-en">Model:</span></strong> '
            f'<span class="model-value">{esc(display or "-")}</span>'
            "</div></div>"
            f'<a class="product-wa-round" href="{esc(wa)}" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp quote">'
            f'<img src="{WHATSAPP_ICON}" alt="">'
            "</a></div>"
        )

    return f'            <article class="product-card" {attrs} hidden>{body}</article>'


def main():
    with CATALOG_JSON.open(encoding="utf-8") as f:
        data = json.load(f)

    cards = []
    for i, product in enumerate(data.get("products", [])):
        if not is_show_true(product.get("show")):
            continue
        product = dict(product)
        product["_csvOrder"] = product.get("_csvOrder", i)
        cards.append(build_card(product))

    block = (
        "        <!-- catalog-static:start -->\n"
        + "\n".join(cards)
        + "\n        <!-- catalog-static:end -->"
    )

    html_text = PRODUCTS_HTML.read_text(encoding="utf-8")

    # Remove bottom SEO sections
    html_text = re.sub(
        r"\n        <section class=\"catalog-seo-intro\"[\s\S]*?</section>\n        <section class=\"catalog-seo-index\"[\s\S]*?</section>",
        "",
        html_text,
        count=1,
    )

    # Replace catalog-root contents
    html_text = re.sub(
        r"<div id=\"catalog-root\" class=\"catalog-grid\" aria-live=\"polite\">[\s\S]*?</div>\n        <nav id=\"catalog-pagination\"",
        '<div id="catalog-root" class="catalog-grid" aria-live="polite">\n'
        + block
        + '\n        </div>\n        <nav id="catalog-pagination"',
        html_text,
        count=1,
    )

    # Status: not loading
    html_text = html_text.replace(
        '<div id="status-area" class="status-msg loading">Loading catalog...</div>',
        '<div id="status-area" class="status-msg loading" hidden></div>',
    )

    PRODUCTS_HTML.write_text(html_text, encoding="utf-8")
    print(f"Embedded {len(cards)} static cards into products.html")


if __name__ == "__main__":
    main()
