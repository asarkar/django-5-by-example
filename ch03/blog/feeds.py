from datetime import datetime

import markdown
from django.contrib.syndication.views import Feed
from django.db.models import QuerySet
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy

from .models import Post


# _Item (the item type) and _Object (the object type for the feed)
class LatestPostsFeed(Feed[Post, None]):
    title = "My blog"
    link = reverse_lazy("blog:post_list")
    description = "New posts of my blog."

    def items(self) -> QuerySet[Post]:
        return Post.published.all()[:5]

    def item_title(self, item: Post) -> str:
        return item.title

    def item_description(self, item: Post) -> str:
        return truncatewords_html(markdown.markdown(item.body), 30)

    def item_pubdate(self, item: Post) -> datetime:
        return item.publish
