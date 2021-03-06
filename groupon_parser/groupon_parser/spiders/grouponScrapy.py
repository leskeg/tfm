# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
from groupon_parser.items import GrouponParserItem
from datetime import datetime
from dateutil import tz
from ipdb import set_trace
import re
import time

class GrouponSpider(scrapy.Spider):
	name = "grouponScrapy"
	allowed_domains = ["groupon.es"]
	start_urls = (
		'http://www.groupon.es/getaways',
	)

	def __init__(self):
		self.driver = webdriver.Firefox()

	def parse(self, response):
		browser = self.driver
		browser.get(response.url)
		try:
			browser.find_element_by_id("already-registered-link").click()
		except:
			browser.find_element_by_xpath('//*[@id="continue"]').click()

		browser.find_element_by_xpath('//*[@id="search_getaways_widget"]/ul/li[1]/div[2]/a').click()

		while True:
			try:
				browser.find_element_by_id('show_more_deals').click()
				time.sleep(4)
			except:
				break

		ad_list = browser.find_elements_by_tag_name("figure")

		for ad in ad_list:
			url = ad.find_element_by_tag_name('a').get_attribute('href')

			try:
				location = ad.find_element_by_class_name('deal-location').text
			except:
				location = ''

			yield scrapy.http.Request(url = url, meta = {'location': location}, callback=self.parse_ad)

		browser.close()

	def parse_ad(self, response):
		item = GrouponParserItem()
		item['url'] = response.url
		item['timestamp'] = datetime.now(tz.tzlocal()).strftime("%y-%m-%d %H:%M:%S:%f%z")
		item['location'] = response.meta['location']

		item_dict = {
			'title': 		'//*[@class="deal-page-title"]/text()',
			'price': 		'//*[@id="deal-hero-price"]/span[2]/text()',
			'discount': 	'//*[@id="purchase-cluster"]/div[3]/table/tbody/tr[2]/td[2]/text()',
			'description':	'//*[@id="tabs-1"]/div/article[1]/div//text()',
			'address': 		'//*[@id="redemption-locations"]/li/div[2]/p[2]/text()',
			'place': 		'//*[@id="redemption-locations"]/li/div[2]/p[1]/strong/text()',
			'options':		'//*[@id="tabs-1"]/div/article[2]/div[2]//text()'
		}

		for key,value in item_dict.iteritems():
			try:
				item[key] = ''.join(response.xpath(value).extract()).strip().replace('\n',' ')
			except:
				item[key] = None

		found = None
		if '*' in item['title']:
			found = 'title'
		elif '*' in item['description']:
			found = 'description'

		if found:
			try:
				item['stars'] = int( item[ found ][ item[ found ].index('*')-1 ] )
			except:
				item['stars'] = None
		else:
			item['stars'] = None

		try:
			item['price'] = int(item['price'].split()[0])
		except:
			item['price'] = None

		try:
			item['discount'] = int(re.findall('\d+',item['discount'])[0])
		except:
			item['discount'] = None

		# item['destiny'] = ''

		yield item