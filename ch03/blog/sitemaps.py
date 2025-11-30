from datetime import datetime

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet

from .models import Post


class PostSitemap(Sitemap[Post]):
    changefreq = "weekly"
    priority = 0.9

    def items(self) -> QuerySet[Post]:
        return Post.published.all()

    def lastmod(self, obj: Post) -> datetime:
        return obj.updated
