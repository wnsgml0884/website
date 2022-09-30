from operator import mod
from unicodedata import category
from xml.etree.ElementTree import Comment
from django.shortcuts import render,redirect
from django.views.generic import ListView, DetailView,CreateView,UpdateView
from django.utils.text import slugify
from .models import Post,Category, Tag, Comment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from .forms import CommentForm
from django.shortcuts import get_object_or_404
from django.db.models import Q



class PostList(ListView):
    model = Post
    ordering = '-pk'

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count']=Post.objects.filter(category=None).count()

        return context
        
def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    post_list = tag.post_set.all()

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list':post_list,
            'tag':tag,
            'categories': Category.objects.all(),
            'no_category_post_count':Post.objects.filter(category=None).count(),
        }
    )

def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category= None)
    else:
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category= category)

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list':post_list,
            # 포스트 중에서 Category.objects.get(slug=slug)로 필터링 한 카테고리만 가져와라
            'categories': Category.objects.all(),
            # categories는 페이지 오른쪽에 위한 카테고리 채워줘라
            'no_category_post_count':Post.objects.filter(category=None).count(),
            # 'no_category_post_count' : 미분류 개수를 알려줘라
            'category':category,
            # 페이지 타이틀 옆에 카테고리 이름을 알려줌
        }
    )

def new_comment(request, pk):
    if request.user.is_authenticated:  
        post = get_object_or_404(Post, pk=pk) # pk가 없으면 오류 발생

        if request.method == 'POST': # submit 버튼을 클릭하면 post방식으로 전달한다.
            comment_form = CommentForm(request.POST) # 폼을 작성하고 들어온 정보들을 폼의 형태 가져온다
            if comment_form.is_valid(): # 폼이 유효하다면 이 밑에 식들을 처리하겠다.
                comment = comment_form.save(commit=False) # 저장기능을 잠시 미루고 댓글 객체만 가져온다.
                comment.post = post
                comment.author = request.user
                comment.save() # 끝나고 나서 저장하겠다.
                return redirect(comment.get_absolute_url()) # 이 주소로 리다이렉트함.

            else:
                return redirect(comment.get_absolute_url())
    else:
        raise PermissionDenied # 로그인하지 않은 상태에서 새로운 댓글에 접근하려는 시도가 있으면
        # 그런 경우 PermissionDenied 호출하겠다.

# indext함수를 대체하는 postlist 클래스

class PostDetail(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count']=Post.objects.filter(category=None).count()
        context['comment_form']=CommentForm
        return context


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']

    template_name = 'blog/post_update_form.html'

    def get_context_data(self, **kwargs):
        context = super(PostUpdate, self).get_context_data()
        if self.object.tags.exists():
            tags_str_list = list()
            for t in self.object.tags.all():
                tags_str_list.append(t.name)
            context['tags_str_default'] = '; '.join(tags_str_list)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        self.object.tags.clear()

        tags_str = self.request.POST.get('tags_str')
        if tags_str:
            tags_str = tags_str.strip()
            tags_str = tags_str.replace(',', ';')
            tags_list = tags_str.split(';')

            for t in tags_list:
                t = t.strip()
                tag, is_tag_created = Tag.objects.get_or_create(name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tags.add(tag)

        return response

    

class PostCreate(LoginRequiredMixin, UserPassesTestMixin,CreateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
    # 최고 관리자 또는 스태프만 접근하도록 제한
    def form_valid(self, form):
        current_user = self.request.user # 웹 사이트 방문자를 의미
        if current_user.is_authenticated and (current_user.is_staff or current_user.is_superuser): # 방문자가 로그인 상태인지 아닌지를 의미
            form.instance.author = current_user # instance(새로 생성한 포스트)의 author 필드에 current_user를 담는다.
            response = super(PostCreate, self).form_valid(form) # creatview의 form_valid함수의 결과값을 변수에 대입
            tags_str = self.request.POST.get('tags_str') # post방식으로 전달된 정보 중에 tags_str값인  input값을 가져와라
            if tags_str:
                tags_str = tags_str.strip()
                tags_str = tags_str.replace(',',';')
                tags_list = tags_str.split(';')
            # 이 값이 빈칸인 경우에는 태그와 관련된 어떤 동작 할 필요가 없다.
            # 여러개의 태그가 들어오더라도 처리할 수 있도록 구문 작성
            # 세미콜론, 쉼표를 구분자로 처리
            # tags_str로 받은 값의 쉼표,세미콜론 모두 세미콜론 변경 한 후 
            # split해서 리스터 형태 담겠다.

                for t in tags_list:
                    t = t.strip() 
                    tag, is_tag_cearted = Tag.objects.get_or_create(name=t)

                    if is_tag_cearted:
                        tag.slug = slugify(t, allow_unicode=True)
                        tag.save()
                    self.object.tags.add(tag)
        # 만약 같은 name을 갖는 태그가 없어 새로 생성을 했다면 아직 slug 값은 없는 상태이므로 slug값을 생성해야 한다.
        # get_or_create메서드를 생성했기 때문에 관리자에서 처리 안해도 가능하다.
        # allow_unicode=True 한글 입력해도 에러 나지 않도록 처리하기 위해서 
            return response
        else:
            return redirect('/blog') # 방문자가 로그인하지 하지 않은 상태라면 블로그 경로로 돌려주겠다.


class CommentUpdate(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(CommentUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post = comment.post
    if request.user.is_authenticated and request.user == comment.author:  
        comment.delete()
        return redirect(comment.get_absolute_url()) # 이 주소로 리다이렉트함.

    else:
        raise PermissionDenied


class PostSearch(PostList):
    paginate_by: None # 한페이지에 다 보여주기 위해서 

    def get_queryset(self):
        q = self.kwargs['q']
        post_list = Post.objects.filter(
            Q(title__contains=q) | Q(tags__name__contains=q)
        ).distinct()
        return post_list

    def get_context_data(self, **kwargs):
        context = super(PostSearch, self).get_context_data()
        q = self.kwargs['q']
        context['search_info'] = f'Search: {q} ({self.get_queryset().count()})'
        return context


# def index(request):
#     posts = Post.objects.all().order_by('-pk') #모든 레코드 가져오는데 최신순으로 보여주기

#     return render(
#         request,
#         'blog/index.html',
#         {
#             'posts':posts,
#         }
#     )

# def single_post_page(request, pk):
#     post = Post.objects.get(pk=pk)

#     return render(
#         request,
#         'blog/single_post_page.html',
#         {
#             'post':post,
#         }
#     )