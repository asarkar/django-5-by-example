from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Post


def post_list(request: HttpRequest) -> HttpResponse:
    posts = Post.published.all()
    return render(request, "blog/post/list.html", {"posts": posts})


def post_detail(request: HttpRequest, id: Any) -> HttpResponse:
    # try:
    #     post = Post.published.get(id=_id)
    # except Post.DoesNotExist:
    #     raise Http404("No Post found.")
    post = get_object_or_404(Post, id=id, status=Post.Status.PUBLISHED)

    return render(request, "blog/post/detail.html", {"post": post})
