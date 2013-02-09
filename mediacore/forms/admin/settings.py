# This file is a part of MediaCore CE (http://www.mediacorecommunity.org),
# Copyright 2009-2013 MediaCore Inc., Felix Schwarz and other contributors.
# For the exact contribution history, see the git revision log.
# The source code contained in this file is licensed under the GPLv3 or
# (at your option) any later version.
# See LICENSE.txt in the main project directory, for more information.

from operator import itemgetter

from babel.core import Locale
from pylons import request
from tw.forms import RadioButtonList, SingleSelectField
from tw.forms.fields import CheckBox
from tw.forms.validators import (Bool, FieldStorageUploadConverter,
    Int, OneOf, Regex, StringBool)

from mediacore.forms import (FileField, ListFieldSet, ListForm,
    SubmitButton, TextArea, TextField, XHTMLTextArea,
    email_validator, email_list_validator)
from mediacore.forms.admin.categories import category_options
from mediacore.lib.i18n import N_, _, get_available_locales
from mediacore.plugin import events

from mediacore.model.settings import insert_settings

comments_enable_disable = lambda: (
    ('mediacore', _("Built-in comments")),
    ('facebook', _('Facebook comments (requires a Facebook application ID)')),
    ('disabled', _('Disable comments')),
)
comments_enable_validator = OneOf(('mediacore', 'facebook', 'disabled'))

title_options = lambda: (
    ('prepend', _('Prepend')),
    ('append', _('Append')),
)
rich_text_editors = lambda: (
    ('plain', _('Plain <textarea> fields (0kB)')),
    ('tinymce', _('Enable TinyMCE for <textarea> fields accepting XHTML (281kB)')),
)
rich_text_editors_validator = OneOf(('plain', 'tinymce'))
navbar_colors = lambda: (
    ('brown', _('Brown')),
    ('blue', _('Blue')),
    ('green', _('Green')),
    ('tan', _('Tan')),
    ('white', _('White')),
    ('purple', _('Purple')),
    ('black', _('Black')),
)

hex_validation_regex = "^#\w{3,6}$"
# End Appearance Settings #

def languages():
    # Note the extra space between English and [en]. This makes it sort above
    # the other translations of english, but is invisible to the user.
    result = [('en', u'English  [en]')]
    for name in get_available_locales():
        locale = Locale.parse(name)
        lang = locale.languages[locale.language].capitalize()
        if locale.territory:
            lang += u' (%s)' % locale.territories[locale.territory]
        else:
            lang += u' '
        lang += u' [%s]' % locale
        result.append((name, lang))
    result.sort(key=itemgetter(1))
    return result


def boolean_radiobuttonlist(name, **kwargs):
    return RadioButtonList(
        name,
        options=lambda: ((True, _('Yes')), (False, _('No'))),
        validator=StringBool,
        **kwargs
    )

class MediacoreSettingsForm(ListForm):
    """
    Abstract class
    Allows definition of class variable to assign defaults to form items
    """
    def __init__(self, *args, **kwargs):
        ListForm.__init__(self, *args, **kwargs)
        if hasattr(self, 'default_values'):
            insert_settings(self.default_values)

class NotificationsForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.NotificationsForm
    
    fields = [
        ListFieldSet('email', suppress_label=True, legend=N_('Email Notifications:'), css_classes=['details_fieldset'], children=[
            TextField('email_media_uploaded', validator=email_list_validator, label_text=N_('Media Uploaded'), maxlength=255),
            TextField('email_comment_posted', validator=email_list_validator, label_text=N_('Comment Posted'), maxlength=255),
            TextField('email_support_requests', validator=email_list_validator, label_text=N_('Support Requested'), maxlength=255),
            TextField('email_send_from', validator=email_validator, label_text=N_('Send Emails From'), maxlength=255),
        ]),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]


class PopularityForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.PopularityForm
    
    fields = [
        ListFieldSet('popularity',
            suppress_label=True,
            css_classes=['details_fieldset'],
            legend=N_('Popularity Algorithm Variables:'),
            children=[
                TextField('popularity_decay_exponent', validator=Int(not_empty=True, min=1), label_text=N_('Decay Exponent')),
                TextField('popularity_decay_lifetime', validator=Int(not_empty=True, min=1), label_text=N_('Decay Lifetime')),
            ]
        ),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class MegaByteValidator(Int):
    """
    Integer Validator that accepts megabytes and translates to bytes.
    """
    def _to_python(self, value, state=None):
        try:
            value = int(value) * 1024 ** 2
        except ValueError:
            pass
        return super(MegaByteValidator, self)._to_python(value, state)

    def _from_python(self, value, state):
        try:
            value = int(value) / 1024 ** 4
        except ValueError:
            pass
        return super(MegaByteValidator, self)._from_python(value, state)

class LegalDomainsValidator(Regex):
    regex = r"^[a-zA-Z_0-9\-\., ]*$"

class UploadForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.UploadForm

    default_values = [
        ('restrict_domains_enabled', u''), #false
        ('illegal_domain_message', u'Your email has to be from the specified domain(s).'),
        ('legal_domains', u''),
        ('requires_confirmation_enabled', u''),
        ('username', u'{email}'),
        ('limited_permissions_group', u'ReviewPublishOwnOnly'),
        ('please_confirm_message', u'Greetings {yourname},\n\nSomeone (probably you) has recently uploaded an item onto {sitename}.\n\nPlease confirm this action and activate your account by clicking the link:\n\n{confirmation_url}\n\nYour new account will be activated and a subsequent email will follow.\n\nIf you have not uploaded anything, please ignore this notice.\n\nRegards,\n{site_name} Admin\n{email_send_from}'),
        ('confirmed_message', u'Thank you for confirming your {sitename} account.\n\nYour account details are as follows:\n\nUsername: {username}\n\nYou will be prompted to enter a new password if you haven\'t changed it already.\n\nSincerely,\n{sitename} Admin{email_send_from}'),
        ]
    
    fields = [
        TextField('max_upload_size', label_text=N_('Max. allowed upload file size in megabytes'), validator=MegaByteValidator(not_empty=True, min=0)),
        ListFieldSet('restrict_domains', suppress_label=True,
                     legend=N_('User upload requires email address from specified domain(s):'),
                     css_classes=['details_fieldset'], children=[
            CheckBox('restrict_domains_enabled', label_text=N_('Enabled'), css_classes=['checkbox-left'], validator=Bool(if_missing='')),
            TextField('illegal_domain_message', label_text=N_('Invalid domain message'), validator=None),
            TextArea('legal_domains', label_text=N_('Domains'), validator=LegalDomainsValidator(),
                      help_text=N_(u'Use commas to delineate multiple domains')),
            ]),
        ListFieldSet('requires_confirmation', suppress_label=True,
                     legend=N_('Create accounts on first upload with limited permissions:'),
                     css_classes=['details_fieldset'], children=[
            CheckBox('requires_confirmation_enabled', label_text=N_('Enabled'), css_classes=['checkbox-left'], validator=Bool(if_missing='')),
            TextField('username', label_text=N_('Username'), validator=None,
                      help_text=N_(u'{email} {handle}')),
            TextField('limited_permissions_group', label_text=N_('Assigned Group'), validator=None, disabled=True,
                      help_text=N_(u'Users in the {} group only have permission to review and publish their own uploads. Users can be promoted by de-assigning this group and assigning other groups (such as "Editor") in "Users" settings. The name of this group cannot be changed to ensure functionality.'.format(request.settings.get('limited_group_name', '')))),
            TextArea('please_confirm_message', label_text=N_('Please confirm message'), validator=None,
                      help_text=N_(u'{confirmation_url} {sitename} {yourname} {email} {username} {email_send_from}')),
            TextArea('confirmed_message', label_text=N_('Confirmed message'), validator=None,
                      help_text=N_(u'{sitename} {yourname} {email} {username} {email_send_from}')),
            ]),
        ListFieldSet('legal_wording', suppress_label=True, legend=N_('Legal Wording:'), css_classes=['details_fieldset'], children=[
            XHTMLTextArea('wording_user_uploads', label_text=N_('User Uploads'), attrs=dict(rows=15, cols=25),
                          help_text=N_(u'{sitename} {yourname} {email} {username}')),
        ]),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class AnalyticsForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.AnalyticsForm
    
    fields = [
        ListFieldSet('google', suppress_label=True, legend=N_('Google Analytics Details:'), css_classes=['details_fieldset'], children=[
            TextField('google_analytics_uacct', maxlength=255, label_text=N_('Tracking Code')),
        ]),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class SiteMapsForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.SiteMapsForm
    
    fields = [
        ListFieldSet('rss', suppress_label=True,
            legend='',
            css_classes=['details_fieldset'],
            children=[
                CheckBox('sitemaps_display',
                    css_classes=['checkbox-left'],
                    label_text=N_('Site Maps'),
                    validator=Bool(if_missing='')),
                CheckBox('rss_display',
                    css_classes=['checkbox-left'],
                    label_text=N_('RSS Feeds'),
                    validator=Bool(if_missing='')),
            ]
        ),
        ListFieldSet('feeds',
            suppress_label=True,
            css_classes=['details_fieldset'],
            legend=N_('RSS Feed Defaults:'),
            children=[
                TextField(u'default_feed_results', validator=Int(not_empty=True, min=1, if_missing=30), 
                    label_text=N_(u'number of items'),
                    help_text=N_(u'The number of items in the feed can be overriden per request '
                                 U'if you add "?limit=X" to the feed URL. If the "limit" parameter '
                                 u'is absent, the default above is used.'),
                ),
            ]
        ),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class GeneralForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.GeneralForm
    
    fields = [
        ListFieldSet('general', suppress_label=True, legend=N_('General Settings:'), css_classes=['details_fieldset'], children=[
            TextField('general_site_name', maxlength=255,
                label_text=N_('Site Name')),
            SingleSelectField('general_site_title_display_order',
                label_text=N_('Display Site Name'),
                options=title_options,
            ),
            SingleSelectField('primary_language',
                label_text=N_('Default Language'), # TODO v0.9.1: Change to 'Primary Language'
                options=languages,
            ),
            SingleSelectField('featured_category',
                label_text=N_('Featured Category'),
                options=category_options,
                validator=Int(),
            ),
            RadioButtonList('rich_text_editor',
                label_text=N_('Rich Text Editing'),
                options=rich_text_editors,
                validator=rich_text_editors_validator,
            ),
        ]),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class CommentsForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.CommentsForm
    
    fields = [
       RadioButtonList('comments_engine',
            label_text=N_('Comment Engine'),
            options=comments_enable_disable,
            validator=comments_enable_validator,
        ),
        ListFieldSet('builtin', suppress_label=True, legend=N_('Built-in Comments:'), css_classes=['details_fieldset'], children=[

            CheckBox('req_comment_approval',
                label_text=N_('Moderation'),
                help_text=N_('Require comments to be approved by an admin'),
                css_classes=['checkbox-inline-help'],
                validator=Bool(if_missing='')),
            TextField('akismet_key', label_text=N_('Akismet Key')),
            TextField('akismet_url', label_text=N_('Akismet URL')),
            TextArea('vulgarity_filtered_words', label_text=N_('Filtered Words'),
                attrs=dict(rows=3, cols=15),
                help_text=N_('Enter words to be filtered separated by a comma.')),
        ]),
        ListFieldSet('facebook', suppress_label=True, legend=N_('Facebook Comments:'), css_classes=['details_fieldset'], children=[
            TextField('facebook_appid', label_text=N_('Application ID'),
                help_text=N_('See: https://developers.facebook.com/apps')),
        ]),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class APIForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.APIForm
    
    fields = [
        boolean_radiobuttonlist('api_secret_key_required', label_text=N_('Require a key to access the API')),
        ListFieldSet('key', suppress_label=True, legend=N_('API Key:'), css_classes=['details_fieldset'], children=[
            TextField('api_secret_key', label_text=N_('Access Key')),
        ]),
        ListFieldSet('prefs', suppress_label=True, legend=N_('API Settings:'), css_classes=['details_fieldset'], children=[
            TextField('api_media_max_results', label_text=N_('Max media results')),
            TextField('api_tree_max_depth', label_text=N_('Max tree depth')),
        ]),
        SubmitButton('save', default='Save', css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]

class AppearanceForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.AppearanceForm
    
    fields = [
        ListFieldSet('general', suppress_label=True, legend=N_('General'),
            css_classes=['details_fieldset'],
            children=[
                FileField('appearance_logo', label_text=N_('Logo'),
                    validator=FieldStorageUploadConverter(not_empty=False,
                        label_text=N_('Upload Logo')),
                    css_classes=[],
                    default=lambda: request.settings.get('appearance_logo', \
                                                             'logo.png'),
                    template='./admin/settings/appearance_input_field.html'),
                FileField('appearance_background_image', label_text=N_('Background Image'),
                    validator=FieldStorageUploadConverter(not_empty=False,
                        label_text=N_('Upload Background')),
                    css_classes=[],
                    default=lambda: request.settings.get('appearance_background_image', \
                                                             'bg_image.png'),
                    template='./admin/settings/appearance_input_field.html'),
                TextField('appearance_background_color', maxlength=255,
                    label_text=N_('Background color'),
                    validator=Regex(hex_validation_regex, strip=True)),
                TextField('appearance_link_color', maxlength=255,
                    label_text=N_('Link color'),
                    validator=Regex(hex_validation_regex, strip=True)),
                TextField('appearance_visited_link_color', maxlength=255,
                    label_text=N_('Visited Link color'),
                    validator=Regex(hex_validation_regex, strip=True)),
                TextField('appearance_text_color', maxlength=255,
                    validator=Regex(hex_validation_regex, strip=True),
                    label_text=N_('Text color')),
                TextField('appearance_heading_color', maxlength=255,
                    label_text=N_('Heading color'),
                    validator=Regex(hex_validation_regex, strip=True)),
                SingleSelectField('appearance_navigation_bar_color',
                    label_text=N_('Color Scheme'),
                    options=navbar_colors),
            ]
        ),
        ListFieldSet('options', suppress_label=True, legend=N_('Options'),
            css_classes=['details_fieldset'],
            children=[
                CheckBox('appearance_enable_cooliris',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Cooliris on the Explore Page'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_enable_featured_items',
                    label_text=N_('Enable Featured Items on the Explore Page'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_enable_podcast_tab',
                    label_text=N_('Enable Podcast Tab'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_enable_user_uploads',
                    label_text=N_('Enable User Uploads'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_enable_widescreen_view',
                    label_text=N_('Enable widescreen media player by default'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_display_logo',
                    label_text=N_('Display Logo'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_display_background_image',
                    label_text=N_('Display Background Image'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_display_mediacore_footer',
                    label_text=N_('Display MediaCore Footer'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
                CheckBox('appearance_display_mediacore_credits',
                    label_text=N_('Display MediaCore Credits in Footer'),
                    css_classes=['checkbox-left'],
                    validator=Bool(if_missing='')),
            ],
            template='./admin/settings/appearance_list_fieldset.html',
        ),
        ListFieldSet('player', suppress_label=True, legend=N_('Player Menu Options'),
            css_classes=['details_fieldset'],
            children=[
                CheckBox('appearance_show_download',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Download button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_share',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Share button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_embed',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Embed button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_widescreen',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Widescreen toggle button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_popout',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Popout button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_like',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Like button on player menu bar.'),
                    validator=Bool(if_missing='')),
                CheckBox('appearance_show_dislike',
                    css_classes=['checkbox-left'],
                    label_text=N_('Enable Dislike button on player menu bar.'),
                    validator=Bool(if_missing='')),
            ],
            template='./admin/settings/appearance_list_fieldset.html',
        ),
        ListFieldSet('advanced', suppress_label=True, legend=N_('Advanced'),
            css_classes=['details_fieldset'],
            children=[
                TextArea('appearance_custom_css',
                    label_text=N_('Custom CSS'),
                    attrs=dict(rows=15, cols=25)),
                TextArea('appearance_custom_header_html',
                    label_text=N_('Custom Header HTML'),
                    attrs=dict(rows=15, cols=25)),
                TextArea('appearance_custom_footer_html',
                    label_text=N_('Custom Footer HTML'),
                    attrs=dict(rows=15, cols=25)),
                TextArea('appearance_custom_head_tags',
                    label_text=N_('Custom <head> Tags'),
                    help_text=N_('These HTML tags are inserted into the HTML '
                        '<head> section. Bad input can cause ugly rendering of '
                        'your site. You can always restore your page by '
                        'the box above.'),
                    attrs=dict(rows=15, cols=25)),
            ],
        ),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
        SubmitButton('reset', default=N_('Reset to Defaults'),
            css_classes=['btn', 'btn-cancel', 'reset-confirm']),
    ]

class AdvertisingForm(MediacoreSettingsForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    
    event = events.Admin.Settings.AdvertisingForm
    
    fields = [
        ListFieldSet('advanced', suppress_label=True, legend='',
            css_classes=['details_fieldset'],
            children=[
                TextArea('advertising_banner_html',
                    label_text=N_('Banner HTML'),
                    attrs=dict(rows=15, cols=25)),
                TextArea('advertising_sidebar_html',
                    label_text=N_('Sidebar HTML'),
                    attrs=dict(rows=15, cols=25)),
            ],
        ),
        SubmitButton('save', default=N_('Save'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
    ]


