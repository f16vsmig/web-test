from django import forms
from .models import Board, Images, Comment, SubComment


class PostForm(forms.ModelForm):
    # title = forms.CharField(max_length=128)
    # body = forms.CharField(max_length=245, label="Item Description.")

    class Meta:
        model = Board
        # fields = '__all__'
        fields = ('notice', 'building', 'title', 'memo',)
        widgets = {
            'notice':  forms.CheckboxInput(
                attrs={
                    'class': 'required form-check-input'
                }
            ),
            'building': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '제목을 입력하세요.'
                }
            ),
            'memo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '내용을 입력하세요.'
                }
            )
        }

    # def __init__(self, *args, **kwargs):
    #     # self.user = kwargs.pop('user')
    #     self.request = kwargs.pop('request', None)
    #     super().__init__(*args, **kwargs)
    #     for field in iter(self.fields):
    #         #get current classes from Meta
    #         classes = self.fields[field].widget.attrs.get("class")
    #         if classes is not None:
    #             classes += " form-control"
    #         else:
    #             classes = "form-control"
    #         self.fields[field].widget.attrs.update({
    #             'class': classes
    #         })


class ImageForm(forms.ModelForm):

    class Meta:
        model = Images
        fields = ('image', )
        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'custom-file-input'
                }
            ),
        }

    # def __init__(self, *args, **kwargs):
    #     # self.user = kwargs.pop('user')
    #     self.request = kwargs.pop('request', None)
    #     super().__init__(*args, **kwargs)
    #     for field in iter(self.fields):
    #         #get current classes from Meta
    #         classes = self.fields[field].widget.attrs.get("class")
    #         if classes is not None:
    #             classes += " form-control-file"
    #         else:
    #             classes = "form-control-file"
    #         self.fields[field].widget.attrs.update({
    #             'class': classes
    #         })


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(
                attrs={
                    'class': 'comment-area',
                    'cols': False,
                    'rows': False,
                    'required': True
                }
            ),
        }


class SubCommentForm(forms.ModelForm):

    class Meta:
        model = SubComment
        fields = ('text',)
