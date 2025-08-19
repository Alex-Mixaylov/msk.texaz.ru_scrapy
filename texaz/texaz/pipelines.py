# texaz/pipelines.py
import openpyxl
from scrapy import signals

class ExcelExportPipeline:
    def __init__(self):
        self.filename = "texaz_output.xlsx"
        self.wb = None
        self.ws = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.close_spider, signal=signals.spider_closed)
        return pipeline

    def open_spider(self, spider):
        # имя файла берём из аргумента паука: scrapy crawl texaz -a filename=foo.xlsx
        self.filename = getattr(spider, "filename", None) or "texaz_output.xlsx"

        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "Data"
        # Заголовки под ваш паук:
        self.ws.append(["Brand", "Sku", "In_Stock", "Price", "List_URL", "Item_URL"])

    def close_spider(self, spider):
        self.wb.save(self.filename)

    def process_item(self, item, spider):
        self.ws.append([
            item.get("Brand"),
            item.get("Sku"),
            item.get("In_Stock"),
            item.get("Price"),
            item.get("List_URL"),
            item.get("Item_URL"),
        ])
        return item
