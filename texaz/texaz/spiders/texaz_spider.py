import re
from urllib.parse import urljoin

import scrapy


class TexazSpider(scrapy.Spider):
    name = "texaz"
    allowed_domains = ["msk.texaz.ru"]

    # Генерируем пагинацию 1..58
    def start_requests(self):
        base = "https://msk.texaz.ru/zapchasti/hidromek/?view=text&PAGEN_1={}"
        for page in range(1, 59):  # 1..58 включительно
            url = base.format(page)
            yield scrapy.Request(url, callback=self.parse_list, cb_kwargs={"list_url": url})

    # --------------------- Вспомогательные ---------------------

    SKU_RX_SLASH = re.compile(r"\b[0-9A-Z]{2,}(?:/[0-9A-Z]+)+\b")
    SKU_RX_PLAIN = re.compile(r"\b[0-9A-Z]{5,}\b")
    STOP_TOKENS = {"VR", "OEM", "ОРИГИНАЛ", "HIDROMEK", "HİDROMEK", "ОРИГ."}

    @staticmethod
    def _clean_price(text: str):
        if not text:
            return None
        # Заменим неразрывные пробелы и выбросим всё, кроме цифр
        digits = re.sub(r"[^\d]", "", text.replace("\xa0", " "))
        return int(digits) if digits else None

    @staticmethod
    def _normalize_stock(text: str):
        if not text:
            return None
        t = " ".join(text.split()).strip()
        if "Под заказ" in t:
            return "Под заказ"
        if "В наличии" in t and "Достаточно" in t:
            return "Достаточно"
        if "В наличии" in t and "Мало" in t:
            return "Мало"
        return t or None

    def _pick_sku_from_title(self, title: str):
        if not title:
            return None
        t = title.upper()
        # приоритет кодов со слешом
        m = self.SKU_RX_SLASH.search(t)
        if m:
            return m.group(0)
        # затем «слитные» коды, игнорируя стоп-слова
        cands = [c for c in self.SKU_RX_PLAIN.findall(t) if c not in self.STOP_TOKENS]
        if len(cands) == 1:
            return cands[0]
        return None

    @staticmethod
    def _strip_prefix(code: str):
        """
        VR-F2826510B -> F2826510B (убираем короткий буквенный префикс перед дефисом)
        """
        if not code:
            return code
        c = code.strip().upper()
        m = re.match(r"^([A-Z]{2,4})-([0-9A-Z/]{4,})$", c)
        return m.group(2) if m else c

    # --------------------- Парсинг списка ----------------------

    def parse_list(self, response, list_url):
        # Каждая карточка товара на "view=text"
        cards = response.css("div.catalog-section-item")
        for card in cards:
            a_rel = card.css("div.catalog-section-item-name a.catalog-section-item-name-wrapper::attr(href)").get()
            title = card.css("div.catalog-section-item-name a.catalog-section-item-name-wrapper::text").get()

            # Наличие
            stock_text = card.css("div.catalog-section-item-quantity::text").get()
            in_stock = self._normalize_stock(stock_text or "")

            # Цена: скидочная -> текущая
            price_text = card.css("div.catalog-section-item-price-discount[data-role='item.price.discount']::text").get()
            if not price_text:
                price_text = card.css("div[data-role='item.price.current']::text").get()
            price = self._clean_price(price_text or "")

            item_url = urljoin(response.url, a_rel) if a_rel else None

            # Пытаемся взять SKU из заголовка
            sku = self._pick_sku_from_title(title or "")
            if sku:
                sku = self._strip_prefix(sku)

            # Если SKU не получилось — переходим на карточку товара
            if not sku and item_url:
                meta = {
                    "brand": "HIDROMEK",
                    "in_stock": in_stock,
                    "price": price,
                    "list_url": list_url,
                    "item_url": item_url,
                }
                yield scrapy.Request(item_url, callback=self.parse_item, meta=meta, dont_filter=True)
            else:
                yield {
                    "Brand": "HIDROMEK",
                    "Sku": sku,
                    "In_Stock": in_stock,
                    "Price": price,
                    "List_URL": list_url,
                    "Item_URL": item_url,
                }

    # --------------------- Парсинг карточки --------------------

    def parse_item(self, response):
        """
        Ищем «Артикул»:
        <div class="catalog-element-section-property-name">Артикул</div>
        <div class="catalog-element-section-property-value">VR-F2826510B</div>
        """
        sku_val = None

        # вариант 1: по XPath «сосед справа»
        sku_val = response.xpath(
            "//div[contains(@class,'catalog-element-section-property-name')][contains(normalize-space(),'Артикул')]/"
            "following-sibling::div[contains(@class,'catalog-element-section-property-value')][1]/text()"
        ).get()

        if sku_val:
            sku_val = self._strip_prefix(sku_val)

        yield {
            "Brand": "HIDROMEK",
            "Sku": sku_val,
            "In_Stock": response.meta.get("in_stock"),
            "Price": response.meta.get("price"),
            "List_URL": response.meta.get("list_url"),
            "Item_URL": response.meta.get("item_url"),
        }
