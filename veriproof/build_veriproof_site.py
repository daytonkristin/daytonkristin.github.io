#!/usr/bin/env python3
"""Offline deterministic VeriProof storefront + launch draft generator (never sends)."""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

BASE=Path(__file__).resolve().parent

def safe_url(u):
    if not isinstance(u,str): raise ValueError("URL must be a string")
    p=urlsplit(u)
    if p.scheme!="https" or not p.hostname or p.username or p.password or any(x in u for x in '<>"'):
        raise ValueError("Public URLs must be safe absolute HTTPS")
    return u

def catalog():
    data=json.loads((BASE/"products.json").read_text(encoding="utf-8"))
    if data.get("brand")!="VeriProof Systems" or data.get("schema_version")!=1:
        raise ValueError("Unexpected catalog brand or schema")
    safe_url(data["site_url"])
    seen=set()
    required={"id","name","category","price_usd","license_model","description",
              "checkout_url","public_proof_url","evaluation_note","llms_description","llms_links"}
    for p in data["products"]:
        if set(p)!=required: raise ValueError("Invalid product fields")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{1,70}",p["id"]) or p["id"] in seen:
            raise ValueError("Invalid or duplicate product identifier")
        seen.add(p["id"])
        if type(p["price_usd"]) is not int or p["price_usd"]<0: raise ValueError("Invalid price")
        for key in ("name","category","license_model","description","evaluation_note","llms_description"):
            if not isinstance(p[key],str) or not p[key].strip(): raise ValueError("Missing product field: "+key)
        safe_url(p["checkout_url"]);safe_url(p["public_proof_url"])
        for link in p["llms_links"]:
            if set(link)!={"label","url"}: raise ValueError("Invalid catalog link")
            safe_url(link["url"])
        if not p["llms_links"] or p["llms_links"][0]!={"label":"Checkout","url":p["checkout_url"]}:
            raise ValueError("Checkout URL mismatch in LLM links")
    return data

def build(data):
    cards=[];sections=[];esc=html.escape
    for p in data["products"]:
        cards.append(
            f'<article class="card"><p class="eyebrow">{esc(p["category"])}</p>'
            f'<h2>{esc(p["name"])}</h2><p class="price">\u0024{p["price_usd"]:,} '
            f'<span class="label">{esc(p["license_model"])}</span></p><p>{esc(p["description"])}</p>'
            f'<a class="cta" href="{esc(p["checkout_url"],quote=True)}">View product / checkout</a>'
            f'<a class="cta" href="{esc(p["public_proof_url"],quote=True)}">Public proof</a>'
            f'<p class="muted">{esc(p["evaluation_note"])}</p></article>')
        block=f'## {p["name"]} — \u0024{p["price_usd"]:,} {p["license_model"]}\n{p["llms_description"]}\n'
        block+=''.join(f'- {link["label"]}: {link["url"]}\n' for link in p["llms_links"])
        sections.append(block+'\n')
    html_template=(BASE/"templates/index.html").read_text(encoding="utf-8")
    llms_template=(BASE/"templates/llms.txt").read_text(encoding="utf-8")
    if html_template.count("{{PRODUCT_CARDS}}")!=1 or llms_template.count("{{PRODUCT_ENTRIES}}")!=1:
        raise ValueError("Nonunique or missing template slot")
    url=safe_url(data["site_url"])
    return {
      "index.html": html_template.replace("{{PRODUCT_CARDS}}","".join(cards)),
      "llms.txt": llms_template.replace("{{PRODUCT_ENTRIES}}","".join(sections)),
      "sitemap.xml": ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             f'<url><loc>{xml_escape(url)}</loc></url>'
             f'<url><loc>{xml_escape(url)}assumption-drift.html</loc></url>'
             f'<url><loc>{xml_escape(url)}rights.html</loc></url></urlset>\n'),
      "robots.txt": (' # Mirror of the host-root crawler preferences; the root file is authoritative.\n'.lstrip()
             + 'User-agent: GPTBot\nUser-agent: Google-Extended\nUser-agent: ClaudeBot\nUser-agent: CCBot\nUser-agent: Bytespider\nUser-agent: Amazonbot\nUser-agent: Applebot-Extended\nDisallow: /\n\n'
             + f'User-agent: *\nAllow: /\nSitemap: {url}sitemap.xml\n')
    }

def launch_drafts(data):
    url=safe_url(data["site_url"])
    names=", ".join(x["name"] for x in data["products"])
    return (
        "# VeriProof Systems — Private launch drafts (NOT APPROVED OR SENT)\n\n"
        f"Public storefront: {url}\nProduct names: {names}\n\n"
        "## Show HN\n"
        "Show HN: VeriProof Systems — proof-first software evaluation\n"
        f"We publish descriptions, prices, public proof and diagnostics for {names}. {url}\n\n"
        "## LinkedIn\n"
        f"VeriProof Systems provides a public evaluation storefront for {names}, "
        f"including proof repositories and product disclosures. {url}\n\n"
        "## Reddit\n"
        f"Looking for feedback on our proof-first software storefront for {names}. "
        f"Products, licensing and diagnostic links are at {url}\n\n"
        "Disclosure: Draft only. No claims of proven adoption or independent certification.\n"
    )

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--launch-drafts",action="store_true")
    args=parser.parse_args()
    data=catalog()
    changed=[]
    for filename,content in build(data).items():
        path=BASE/filename
        if args.check:
            if not path.is_file() or path.read_bytes()!=content.encode("utf-8"):
                changed.append(filename)
        else: path.write_text(content,encoding="utf-8")
    if args.launch_drafts:
        path=BASE/"generated/launch-posts.md"
        text=launch_drafts(data)
        if args.check:
            if not path.is_file() or path.read_bytes()!=text.encode("utf-8"):
                changed.append("generated/launch-posts.md")
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_text(text,encoding="utf-8")
    if changed:
        print("BLOCKED: stale assets: "+", ".join(changed),file=sys.stderr)
        return 1
    print("PASS: deterministic storefront generated from "+str(len(data["products"]))+" products")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
