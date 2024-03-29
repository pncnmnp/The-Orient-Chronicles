import pickle
from django.shortcuts import render
from json import load
from . import fetch_news
from .models import Title
from django.http import HttpResponse
from datetime import datetime, timedelta
from os import path
from dateutil import parser

def store(request):
	past_time = datetime.now() - timedelta(seconds=1)
	past_day = datetime.now() - timedelta(hours=6)
	curr_timestamp = datetime.fromtimestamp(path.getmtime('./db.sqlite3'))

	# Checks if it is time to DROP the table.
	# The backup of news is stored in './datasets/past_news/'
	if past_day > curr_timestamp:
		Title.objects.all().delete()

	# Checks if news needs to be updated
	if past_time > curr_timestamp:
		news_obj = fetch_news.Fetch_News()
		news_content = dict()
		if news_obj.check_news() == False:
			news_content = news_obj.get_pickle()
			news_obj.top_news(news_content)
			news_content = news_obj.top_stories
		else:
			news_obj.top_news(news_obj.news_content)
			news_content = news_obj.top_stories

		category_path = './headlines/datasets/categories.json'
		categories = load(open(category_path))

		for category in categories['categories']:
			index = 0
			while(True):
				try:
					datetime_obj = parser.parse(news_content[category][index]['date'])

					# Checks if the news year is same as current year
					# This removes outdated news
					if datetime_obj.year < datetime.now().year:
						index += 1
						continue
					news_instance, created = Title.objects.get_or_create(
						title_text=news_content[category][index]['title'],
						pub_date=datetime_obj,
						defaults={
							'news_url': news_content[category][index]['links'],
							'description': news_content[category][index]['desc'],
							'news_category': category
						}
					)
					if created == True:
						news_instance.save()
					index += 1
				except:
					break

	context = {}
	return render(request, 'headlines/update_and_redirect.html', context)

def fetch(request):
	context = dict()
	category_path = './headlines/datasets/categories.json'
	categories = load(open(category_path))

	# 'context' stores news from all categories,
	# in the DESC. order of their publication date
	for category in categories['categories']:
		context[category+'_list'] = Title.objects.filter(news_category__startswith=category).order_by('-pub_date')

	# Today's date
	context['date'] = str(datetime.now().strftime("%a %b %d, %Y"))

	return render(request, 'headlines/index.html', context)

def custom(request):
	context = dict()
	context['date'] = str(datetime.now().strftime("%a %b %d, %Y"))
	return render(request, 'headlines/custom_feed.html', context)

def get_custom_search(request):
	if request.method == 'POST':
		search = request.POST.get('textfield', None)
		context = dict()
		context['date'] = str(datetime.now().strftime("%a %b %d, %Y"))
		try:
			context['form'] = Title.objects.filter(title_text__icontains=search).order_by('-pub_date')
			if context['form'].exists() == False:
				context['no_result'] = 'No Results Found'
			return render(request, 'headlines/custom_feed.html', context)
		except:
			render(request, 'headlines/custom_feed.html', context)
	else:
		return render(request, 'headlines/custom_feed.html', context={'form': ''})
