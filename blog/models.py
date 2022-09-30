from tabnanny import verbose
from venv import create
from django.db import models
from django.contrib.auth.models import User
import os

class Tag(models.Model):
    name = models.CharField(max_length=50,unique=True)
    slug = models.SlugField(max_length=200,unique=True,allow_unicode=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/blog/tag/{self.slug}/'

class Category(models.Model):
    name = models.CharField(max_length=50,unique=True)
    slug = models.SlugField(max_length=200,unique=True,allow_unicode=True)
# unique=True : 동일한 이름을 갖는 카테고리를 만들 수 없다.
# allow_unicode=True : 한글도 인식하게 하려고

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/blog/category/{self.slug}/'

    class Meta:
        verbose_name_plural = "categories"

class Post(models.Model):
    title = models.CharField(max_length=30) # 최대길이
    hook_text = models.CharField(max_length=100, blank=True)
    content = models.TextField() # 문자열 길이 제한 없다

    head_image = models.ImageField(upload_to='blog/images/%Y/%m/%d/',blank=True)
    file_upload = models.FileField(upload_to='blog/files/%Y/%m/%d/',blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # 현재시간으로 자동저장
    updated_at = models.DateTimeField(auto_now=True) # 다시 저장한 현재시간으로 자동저장

    author = models.ForeignKey(User,null=True, on_delete=models.SET_NULL)
    # on_delete=models.CASCADE : DB에서 작성자가 삭제되면 알아서 포스트도 같이 삭제되라
    # on_delete=models.SET_NULL : 연결된 사용자가 삭제되어도 포스트 남기려고

    category = models.ForeignKey(Category, null = True, blank= True, on_delete=models.SET_NULL)
    # null = True : 카테고리 선택 안하면 미분류처리
    # on_delete=models.SET_NULL : ForeignKey로 연결되어 있던 카테고리가 삭제된 경우 
    # 연결된 포스트까지 삭제되지 않고 해당 포스트의 카테고리 필드만 널이 되도록 처리
    # blank= True : 카테고리를 선택하지 않고 빈칸으로 지정할 수 있다.

    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f'[{self.pk}] {self.title} :: {self.author}'

    def get_absolute_url(self):
        return f'/blog/{self.pk}/'

    def get_file_name(self):
        return os.path.basename(self.file_upload.name)

    def get_file_ext(self):
        return self.get_file_name().split('.')[-1]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.author}::{self.content}'
    
    def get_absolute_url(self):
        return f'{self.post.get_absolute_url()}#comment-{self.pk}'


    def get_avatar_url(self):
        if self.author.socialaccount_set.exists():
            return self.author.socialaccount_set.first().get_avatar_url()
        else:
            return f'http://picsum.photos/60/60'
