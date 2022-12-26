import scrapy
from scrapy.selector import Selector


class TestSpider(scrapy.Spider):
    name = 'florida_spider'
    allowed_domains = ['floridabuy.org']
    mappings = {
        'amendment_files':['amendment','renewal','extension'],
        'contract_files':['award letter','contract award','agreement'],
        'bid_solicitation_files':['bid','rfp','request for proposal','ifb','itb','solicitation','rfq','erfq','specification','scope of services'],
        'bid_tabulation_files':['proposal evaluation','comment & review','tab','performance evaluation','tabulation','vendor response','evaluation matrix'],
        'pricing_files':['price','pricing','discount','catalog'],
    }

    def start_requests(self):
        url = 'https://floridabuy.org/suppliers-vendors/'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        sel = Selector(text=response.text)
        for link in sel.xpath("//a[@class='catlink']/@href").getall():
            yield scrapy.Request(url=link, callback=self.parse_supplier, dont_filter=True)
    
    def parse_supplier(self, response):
        sel = Selector(text=response.text)
        url = response.url
        vendor_name = sel.xpath("//h1[@id='vendor_title']/a/text()").get()
        vendor_website = sel.xpath("//div[@class='entry-content']/p/a/@href").get()
        categories = sel.xpath("//ul[@class='blog-categories']/li/a/text()").getall()
        docs = self.decide_file_type(selector=sel)

        item = {
            "URL":url,
            "Vendor_Name":vendor_name,
            "Vendor_Website":vendor_website,
            "Categories":categories,
            "Docs":docs,
        }     
        yield item   

    def decide_file_type(self, selector):
        docs = {
            "amendment_files":[],
            "contract_files":[],
            "bid_solicitation_files":[],
            "bid_tabulation_files":[],
            "pricing_files":[],
            'other_docs_files':[]
        }
        for doc in selector.xpath("//div[@id='divMsg']//a[contains(@href,'s3.amazonaws.com')]"):
            type_found = False
            doc_url = doc.xpath("./@href").get()
            doc_name = doc.xpath("./text()").get()
            for file_type, values in self.mappings.items():
                for val in values:
                    if val in doc_name.lower():
                        docs[file_type].append(doc_url)
                        type_found = True
            if not type_found:
                docs['other_docs_files'].append(doc_url) 
        return docs