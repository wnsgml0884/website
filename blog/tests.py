import imp
from urllib import response
from django.test import TestCase, Client
from bs4 import BeautifulSoup
from .models import Post

class TestView(TestCase):
    def setUp(self):
        self.client = Client()


    def test_post_list(self):
        # 1.1 포스트 목록 페이지가 가져온다.
        response = self.client.get('/blog/')
        # 1.2 정상적으로 페이지가 로드된다.
        self.assertEqual(response.status_code,200)
        # 1.3 페이지 타이틀을 'Blog'이다.
        soup = BeautifulSoup(response.content,'html.parser')
        self.assertEqual(soup.title.text,'Blog')
        # 1.4 내비게이션바가 있다.
        navbar = soup.nav
        # 1.5 Blog, Abount Me라는 문구가 내비게이션 바에 있다.
        self.assertIn('Blog',navbar.text)
        self.assertIn('About me',navbar.text)
        # 2.1 메인 영역에 게시물이 하나도 없다면
        self.assertEqual(Post.objects.count(),0)
        # 2.2 아직 게시물이 없습니다. 라는 문구가 없다면
        main_area = soup.find('div',id='main-area')
        self.assertIn('아직 게시물이 없습니다.',main_area.text)
        # 3.1 게시물이 2개 있다면
        Post_001 = Post.objects.create(
            title ='첫번째 포스트입니다.',
            content = 'Hello world, we are the world'
        )

        Post_002 = Post.objects.create(
            title ='두번째 포스트입니다.',
            content = '1등이 전부는 아니잖아요'
        )

        self.assertEqual(Post.objects.count(),2)
        # 3.2 포스트 목록 페이지를 새로고침했을 때 
        response = self.client.get('/blog/')
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(response.status_code,200)
        # 3.3 메인 영역에 포스트의 2개의 타이틀이 존재한다.
        main_area = soup.find('div',id='main-area')
        self.assertIn(Post_001.title, main_area.text)
        self.assertIn(Post_002.title, main_area.text)
        # 3.4 아직 게시물이 없습니다라는 문구는 더 이상 보이지 않는다. 
        self.assertNotIn('아직 게시물이 없습니다.',main_area.text)