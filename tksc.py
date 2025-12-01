import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time

@st.cache_data(ttl=1800)  # 30min cache
def scrape_tripplek_catalog(limit=10):
    """Scrape first 10 products from TrippleK shop"""
    url = "https://www.tripplek.co.ke/shop/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        products = []
        product_items = soup.find_all('div', class_='product col_item', limit=limit)
        
        for item in product_items:
            # PRODUCT NAME (from h3 > a)
            name_link = item.find('h3', class_='text-clamp')
            name = name_link.find('a').text.strip() if name_link and name_link.find('a') else "Unknown"
            
            # IMAGE (lazy-loaded data-src)
            img_tag = item.find('img', class_='lazyload')
            image_url = img_tag['data-src'] if img_tag and img_tag.get('data-src') else ""
            
            # PRICE (handles sale prices with <del> and <ins>)
            price_span = item.find('span', class_='price')
            if price_span:
                # Current price (ins tag)
                current_price = price_span.find('ins')
                price_text = current_price.find('span', class_='woocommerce-Price-amount').text.strip() if current_price else "N/A"
                
                # Discount % (if available)
                discount = item.find('div', class_='font80 text-right-align greencolor')
                discount_text = discount.text.strip() if discount else ""
            else:
                price_text = "Price N/A"
                discount_text = ""
            
            products.append({
                'name': name,
                'price': price_text,
                'image_url': image_url,
                'discount': discount_text,
                'url': name_link.find('a')['href'] if name_link else "",
                'specs': f"• Fresh from TrippleK
• {discount_text}
• Official warranty"
            })
        
        return products[:10]
    
    except Exception as e:
        st.error(f"Scrape failed: {str(e)}")
        return []

# 🎬 STREAMLIT CATALOG UI
st.title("📦 TrippleK Live Catalog (10 items)")

if st.button("🔄 Scrape Fresh Catalog", type="primary"):
    with st.spinner("Scraping TrippleK shop..."):
        catalog = scrape_tripplek_catalog(10)
        st.session_state.catalog = catalog
        st.success(f"✅ Scraped {len(catalog)} products!")

# Load catalog (cached or fresh)
if 'catalog' not in st.session_state:
    catalog = scrape_tripplek_catalog(10)
    st.session_state.catalog = catalog

# Catalog Display
st.subheader("📱 Products")
catalog = st.session_state.catalog

if catalog:
    # Product cards
    cols = st.columns(2)
    for i, product in enumerate(catalog):
        with cols[i % 2]:
            st.image(product['image_url'], use_column_width=True)
            st.markdown(f"**{product['name']}**")
            st.markdown(f"*{product['price']}*")
            if st.button(f"🎬 Load Ad", key=f"load_{i}"):
                st.session_state.selected_product = product
                st.success("✅ Product loaded for ad!")
                st.rerun()
    
    # Selection dropdown
    names = [p['name'] for p in catalog]
    selected_name = st.selectbox("Quick Select", names)
    selected_product = next((p for p in catalog if p['name'] == selected_name), None)
    
    if selected_product:
        col1, col2 = st.columns(2)
        with col1:
            st.image(selected_product['image_url'], width=250)
        with col2:
            st.markdown(f"### {selected_product['name']}")
            st.markdown(f"**Price:** {selected_product['price']}")
            st.markdown(f"**Discount:** {selected_product['discount']}")
            st.markdown(f"**Specs:**
{selected_product['specs']}")
        
        # Auto-fill for ad generator
        if st.button("🚀 Use in Ad Generator"):
            st.session_state.product_name = selected_product['name']
            st.session_state.price = selected_product['price']
            st.session_state.specs = selected_product['specs']
            st.success("✅ Ad fields auto-filled!")
            st.rerun()
    
    # Export
    st.download_button(
        "💾 Export Catalog JSON",
        data=json.dumps(catalog, indent=2),
        file_name=f"tripplek_catalog_{int(time.time())}.json",
        mime="application/json"
    )
else:
    st.warning("No products found. Click 'Scrape Fresh Catalog' to retry.")