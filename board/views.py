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
from buildinginfo.models import Building, Analysis
from account.models import User

from .forms import PostForm, ImageForm, CommentForm, SubCommentForm

import math


class BoardView(ListView):
    model = Board
    form_class = CommentForm
    template_name = 'board/board_frame.html'
    paginate_by = 10

    def get_update_url(self):
        return reverse_lazy('board:post_update', kwargs={'pk': self.request.GET.get('id')})

    def get_queryset(self):
        queryset = self.model.objects.filter(notice='False')
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
        block_size = 10  # 하단의 페이지 목록 수
        start_index = int(
            (context['page_obj'].number - 1) / block_size) * block_size
        end_index = min(start_index + block_size,
                        len(context['paginator'].page_range))

        context['start_index'] = start_index
        context['end_index'] = end_index
        context['page_range'] = context['paginator'].page_range[start_index:end_index]
        context['last_page'] = math.ceil(
            self.get_queryset().count()/self.paginate_by)
        context['comment_form'] = self.form_class(prefix="comment")
        context['comment_list'] = Comment.objects.all()
        context['subcomment_list'] = SubComment.objects.all()
        context['photo_list'] = Images.objects.all()
        context['update_url'] = self.get_update_url()
        # 글 조회시 조회수+1, 세부내용과 사진을 콘텍스트에 추가
        if self.request.GET.get('id'):
            post_id = self.request.GET.get('id')
            post_detail = Board.objects.get(pk=post_id)

            # 조회수 +1
            post_detail.hits = post_detail.hits + 1
            post_detail.save()

            context['post_detail'] = post_detail
            # 해당 게시물 오브젝트에 외래키로 연결된 이미지를 context에 추가
            context['photos'] = Images.objects.filter(board=post_detail)
            context['comments'] = Comment.objects.filter(
                board=post_detail).order_by('registration')
            context['subcomments'] = SubComment.objects.filter(
                comment__board=post_detail).order_by('registration')

        return context


class BoardCreateView(CreateView):
    model = Board
    template_name = 'board/post_form.html'
    form_class = PostForm
    images_num = 3
    board_name = 'COMM'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset = modelformset_factory(
            Images, form=ImageForm, extra=self.images_num)
        context['formset'] = formset(queryset=Images.objects.none())
        return context

    def form_valid(self, form):
        ImageFormSet = modelformset_factory(
            Images, form=ImageForm, extra=self.images_num)
        formset = ImageFormSet(
            self.request.POST, self.request.FILES, queryset=Images.objects.none())
        if form.is_valid() and formset.is_valid():
            ### form 저장 ###
            form.save(commit=False)
            form.instance.author = self.request.user
            form.instance.board_name = self.board_name
            form.save()
            ### formset 저장 ###
            for f in formset.cleaned_data:
                if f:
                    image = f['image']
                    photo = Images(board=form.instance, image=image)
                    photo.save()
            return HttpResponseRedirect(self.get_success_url())

        else:
            return self.render_to_response(self.get_context_data(form=form))


class BoardUpdateView(UpdateView):
    model = Board
    template_name = 'board/post_form.html'
    form_class = PostForm
    images_num = 3
    board_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        images = Images.objects.filter(board__pk=self.kwargs['pk'])
        formset = modelformset_factory(
            Images, form=ImageForm, extra=self.images_num-images.count())
        context['images'] = images
        context['formset'] = formset(queryset=Images.objects.none())
        return context

    def form_valid(self, form):
        ImageFormSet = modelformset_factory(
            Images, form=ImageForm, extra=self.images_num)
        formset = ImageFormSet(
            self.request.POST, self.request.FILES, queryset=Images.objects.none())
        if form.is_valid() and formset.is_valid():
            ### form 저장 ###
            form.save()
            ### formset 저장 ###
            for f in formset.cleaned_data:
                if f:
                    image = f['image']
                    photo = Images(board=form.instance, image=image)
                    photo.save()
            return HttpResponseRedirect(self.get_success_url())

        else:
            return self.render_to_response(self.get_context_data(form=form))


def post_delete(request, pk):
    instance = get_object_or_404(Board, pk=pk)
    user = User.objects.get(nickname=request.user)
    if request.method == 'POST':
        if Board.objects.filter(author=user) or user.is_superuser:
            instance.delete()
        else:
            return Http404
    return HttpResponse(status=200)


def image_delete(request, pk):
    model = Images
    instance = get_object_or_404(model, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if instance in model.objects.filter(board__author__email=username) or user_instance.is_superuser:
        instance.delete()
    else:
        return Http404
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def comment_create(request):
    if request.method == 'POST':
        notice_pk = request.GET.get('id')
        notice_instance = get_object_or_404(Board, pk=notice_pk)
        form = CommentForm(request.POST, prefix="comment")
        if form.is_valid():
            comment = form.save(commit=False)
            comment.board = notice_instance
            comment.author = request.user
            comment.save()
            return HttpResponse(status=204)

    return Http404


def comment_delete(request, pk):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, pk=pk)
        user = User.objects.get(nickname=request.user)
        if comment.author == user or user.is_superuser:
            comment.text = ''  # 댓글은 삭제시 실제 삭제하는 대신 삭제문구로 업데이트함
            comment.save()
            return HttpResponse(status=204)

    return Http404


def subcomment_create(request):
    if request.method == 'POST':
        comment_pk = request.GET.get('id')
        comment_instance = Comment.objects.get(pk=comment_pk)
        form = SubCommentForm(request.POST, prefix="subcomment")
        if form.is_valid():
            subcomment = form.save(commit=False)
            subcomment.comment = comment_instance
            subcomment.author = request.user
            subcomment.save()
            return HttpResponse(status=204)

    return Http404


def subcomment_delete(request, pk):
    model = SubComment
    instance = get_object_or_404(model, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if instance in model.objects.filter(author__email=username) or user_instance.is_superuser:
        instance.text = ''  # 댓글은 삭제시 실제 삭제하는 대신 삭제문구로 업데이트함
        instance.save()
    else:
        return Http404
    # return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponse(status=204)


class BuildinginfoBoardView(BoardView):
    template_name = 'board/buildinginfo_board_frame.html'
    board_name = 'COMM'
    extra_context = {
        'navbar': 'buildinginfo',
        'board_name': '커뮤니티'
    }

    def get_update_url(self):
        return reverse_lazy('board:building_board_update',
                            kwargs={'pk': self.request.GET.get('id')})

    def get_queryset(self):
        queryset = super().get_queryset()
        building = Building.objects.get(pk=self.kwargs.get('pk'))
        queryset = self.model.objects.filter(
            board_name=self.board_name, building=building).order_by('-pk')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building = Building.objects.get(pk=self.kwargs['pk'])
        context['building_object'] = building
        context['notice'] = self.model.objects.filter(
            board_name=self.board_name, notice='True').order_by('-registration')
        context['building_list'] = Building.objects.all()
        # context['board_name'] = self.board_name
        board_obj = Board.objects.filter(pk=self.request.GET.get('id')).first()
        context['images'] = Images.objects.filter(board=board_obj)
        return context


class BuildinginfoBoardCreateView(BoardCreateView):
    template_name = 'board/buildinginfo_board_form.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }
    board_name = 'COMM'
    images_num = 5

    def get_success_url(self):
        return reverse_lazy('board:building_board', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ### Set initial ###
        building = Building.objects.get(pk=self.kwargs['pk'])
        form = context['form']
        form.fields["building"].initial = building
        ### 추가 컨텍스트 ###
        context['building_object'] = building
        return context


class BuildinginfoBoardUpdateView(BoardUpdateView):
    template_name = 'board/buildinginfo_board_form.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }
    board_name = 'COMM'
    images_num = 5

    def get_success_url(self):
        return reverse_lazy('board:building_board', kwargs={'pk': self.request.GET.get('building')}) + '?building=' + self.request.GET.get('building') + '&page=' + self.request.GET.get('page') + '&id=' + self.request.GET.get('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ### 추가 컨텍스트 ###
        building = Building.objects.get(pk=self.request.GET.get('building'))
        context['building_object'] = building
        return context


# def buildinginfo_board_create(request, pk):
#     template_name = 'board/buildinginfo_board_form.html'

#     post_form = PostForm()
#     formset = ImageFormSet(queryset=Images.objects.none())
#     building_object = Building.objects.get(pk=pk)
#     context = {
#         'post_form': PostForm(),
#         'formset': formset,
#         'building_object': building_object
#     }
#     context['post_form'] = postForm
#     context['formset'] = formset
#     context['action'] = reverse('board:post_create') + "?board=" + board_name
#     context['building_object'] = building
#     board_name = 'notice'
#     postForm = PostForm()
#     postForm.fields["building"].initial = building
#     ImageFormSet = modelformset_factory(Images, form=ImageForm, extra=3)
#             #'extra' means the number of photos that you can upload   ^
#     formset = ImageFormSet(queryset=Images.objects.none())

#     if request.method == 'POST'
#         postForm = PostForm(request.POST)
#         image_formset = ImageFormSet(request.POST, request.FILES, queryset=Images.objects.none())

#         if postForm.is_valid() and image_formset.is_valid():
#             post_form = postForm.save(commit=False)
#             post_form.board_name = get_board_name(board_name)
#             post_form.author = request.user
#             post_form.save()

#             for image_form in image_formset.cleaned_data:
#                 #this helps to not crash if the user
#                 #do not upload all the photos
#                 if image_form:
#                     image = image_form['image']
#                     photo = Images(board=post_form, image=image)
#                     photo.save()

#                 return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


#     return render(request, template_name, context)
