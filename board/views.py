from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView, FormMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.forms import modelformset_factory
from django.contrib import messages

from .models import Board, Images, Comment, SubComment
from buildinginfo.models import Building
from account.models import User

from .forms import PostForm, ImageForm, CommentForm, SubCommentForm

import math


def get_board_name(key):
    board_dict = {
        'notice': 'N',
        'freeboard': 'FB',
    }
    return board_dict[key]


class BoardView(ListView):
    model = Board
    form_class = CommentForm
    template_name = 'board/board_frame.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = self.model.objects.filter(board_name=get_board_name(self.board_name), notice='False')
        username = self.request.user.get_username()
        user_instance = User.objects.get(email=username)
        if user_instance.is_superuser:
            queryset = queryset.order_by('-pk')
        else:
            queryset = queryset.filter(author=user_instance).order_by('-pk')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 페이지네이션 커스텀
        block_size = 10 # 하단의 페이지 목록 수
        start_index = int((context['page_obj'].number - 1) / block_size) * block_size
        end_index = min(start_index + block_size, len(context['paginator'].page_range))
        
        context['start_index'] = start_index
        context['end_index'] = end_index
        context['page_range'] = context['paginator'].page_range[start_index:end_index]
        context['last_page'] = math.ceil(self.get_queryset().count()/self.paginate_by)
        context['comment_form'] = self.form_class(prefix='comment')
        context['comment_list'] = Comment.objects.all()
        context['subcomment_list'] = SubComment.objects.all()
        context['photo_list'] = Images.objects.all()

        # 글 조회시 조회수+1, 세부내용과 사진을 콘텍스트에 추가
        if self.request.GET.get('id'):
            post_id = self.request.GET.get('id')
            post_detail = Board.objects.get(pk=post_id)

            # 조회수 +1
            post_detail.hits = post_detail.hits + 1
            post_detail.save()

            context['post_detail'] = post_detail
            context['photos'] = Images.objects.filter(board=post_detail) # 해당 게시물 오브젝트에 외래키로 연결된 이미지를 context에 추가
            context['comments'] = Comment.objects.filter(board=post_detail).order_by('registration')
            context['subcomments'] = SubComment.objects.filter(comment__board=post_detail).order_by('registration')
        # 페이지를 콘텍스트에 추가
        if self.request.GET.get('page'):
            context['page'] = self.request.GET.get('page')
        return context

    def get_board_name(self, key):
        board_dict = {
            'notice': 'N',
            'freeboard': 'FB',
        }
        return board_dict[key]


@permission_required('board.add_board', '/permission-denied')
def post_create(request):
    board_name = request.GET.get('board')
    navbar = 'buildinginfo' if board_name == 'notice' else 'communication'

    ImageFormSet = modelformset_factory(Images, form=ImageForm, extra=3)
            #'extra' means the number of photos that you can upload   ^
    if request.method == 'POST':
        postForm = PostForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Images.objects.none())

        if postForm.is_valid() and formset.is_valid():
            post_form = postForm.save(commit=False)
            post_form.board_name = get_board_name(board_name)
            post_form.author = request.user
            post_form.save()

            for form in formset.cleaned_data:
                #this helps to not crash if the user   
                #do not upload all the photos
                if form:
                    image = form['image']
                    photo = Images(board=post_form, image=image)
                    photo.save()
            messages.success(request,
                             "Yeeew, check it out on the home page!")
            return HttpResponse(status=204)
        else:
            print(postForm.errors, formset.errors)
    else:
        postForm = PostForm()
        formset = ImageFormSet(queryset=Images.objects.none())
    return render(request, 'board/post_form.html',
                  {'postForm': postForm, 'formset': formset, 'board_name': board_name, 'navbar': navbar, 'sidebar': board_name})


def post_update(request, pk):
    post_instance = get_object_or_404(Board, pk=pk)
    photo_object_list = Images.objects.filter(board__pk=pk)
    ImageFormSet = modelformset_factory(Images, form=ImageForm, extra=3-photo_object_list.count())
            #'extra' means the number of photos that you can upload   ^
    if request.method == 'POST':
        postForm = PostForm(request.POST, instance=post_instance)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Images.objects.none())

        if postForm.is_valid() and formset.is_valid():
            post_form = postForm.save(commit=False)
            post_form.author = request.user
            post_form.save()

            for form in formset.cleaned_data:
                #this helps to not crash if the user   
                #do not upload all the photos
                if form:
                    image = form['image']
                    photo = Images(board=post_form, image=image)
                    photo.save()
            messages.success(request,
                             "Yeeew, check it out on the home page!")
            return HttpResponse(status=204)
        else:
            print(postForm.errors, formset.errors)
    else:
        postForm = PostForm(instance=post_instance)
        formset = ImageFormSet(queryset=Images.objects.none())
        navbar = 'buildinginfo' if post_instance.board_name == 'N' else 'communication'
        board_name = request.GET.get('board')
        return render(request, 'board/post_form.html',
                {'postForm': postForm, 'formset': formset, 'photo_objects': photo_object_list, 'board_name': board_name, 'navbar': navbar, 'sidebar': board_name})


def post_delete(request, pk):
    model = Board
    instance = get_object_or_404(model, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if request.method == 'POST':
        if instance in model.objects.filter(author__email=username) or user_instance.is_superuser:
            instance.delete()
        else:
            return Http404
    return HttpResponse(status=204)


def image_delete(request, pk):
    model = Images
    instance = get_object_or_404(model, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if instance in model.objects.filter(board__author__email=username) or user_instance.is_superuser:
        instance.delete()
    else:
        Http404
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def comment_create(request):
    if request.method == 'POST':
        notice_pk = request.GET.get('id')
        notice_instance = get_object_or_404(Board, pk=notice_pk)
        form = CommentForm(request.POST, prefix='comment')
        if form.is_valid():
            comment = form.save(commit=False)
            comment.board = notice_instance
            comment.author = request.user
            comment.save()
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponse(status=204)


def comment_delete(request, pk):
    if request.method == 'POST':
        model = Comment
        instance = get_object_or_404(model, pk=pk)
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        if instance in model.objects.filter(author__email=username) or user_instance.is_superuser:
            instance.text = '' # 댓글은 삭제시 실제 삭제하는 대신 삭제문구로 업데이트함
            instance.save()
        else:
            Http404
        # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponse(status=204)


def subcomment_create(request):
    if request.method == 'POST':
        comment_pk = request.GET.get('id')
        comment_instance = get_object_or_404(Comment, pk=comment_pk)
        form = SubCommentForm(request.POST, prefix='subcomment')
        if form.is_valid():
            subcomment = form.save(commit=False)
            subcomment.comment = comment_instance
            subcomment.author = request.user
            subcomment.save()
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponse(status=204)


def subcomment_delete(request, pk):
    model = SubComment
    instance = get_object_or_404(model, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if instance in model.objects.filter(author__email=username) or user_instance.is_superuser:
        instance.text = '' # 댓글은 삭제시 실제 삭제하는 대신 삭제문구로 업데이트함
        instance.save()
    else:
        Http404
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponse(status=204)


