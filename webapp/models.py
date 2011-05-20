# Copyright (C) 2011 Philter Phactory Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE X
# CONSORTIUM BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Except as contained in this notice, the name of Philter Phactory Ltd. shall
# not be used in advertising or otherwise to promote the sale, use or other
# dealings in this Software without prior written authorization from Philter
# Phactory Ltd..
#

from django.db import models
from django.conf import settings
from client import OAuthWrangler, OAuthForbiddenException, OAuthUnauthorizedException
import oauth.oauth as oauth
from django.core.urlresolvers import reverse
import sys
import logging

class ProstheticException(Exception):
    pass
    
class Prosthetic(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    classname = models.CharField(max_length=200) # , choices=[[".","."]])
    server = models.CharField(max_length=200)
    consumer_key = models.CharField(max_length=200)
    consumer_secret = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    show_on_homepage = models.BooleanField(default=False)
    blog_keyword = models.CharField(max_length=200, null=True,blank=True)

    def __unicode__(self):
        return "%s on %s"%(self.name, self.server)
    
    def tokens(self):
        return AccessToken.objects.filter(prosthetic=self)
    
    def wrangler(self):
        return OAuthWrangler(self.server, self.consumer_key, self.consumer_secret, 0)
    
    def get_class(self):
        # do at run time to avoid import import loop
        from introspection import ptk_class_by_name
        return ptk_class_by_name(self.classname)

    def get_absolute_url(self):
        return "http://%s%s"%( settings.LOCAL_SERVER, reverse("webapp.views.prosthetic", args=[ self.id ]))
    
class AccessToken(models.Model):
    """An OAuth Access Token"""
    prosthetic = models.ForeignKey(Prosthetic)
    oauth_key = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField()
    enabled = models.BooleanField()
    
    # for convenient reference, the name of the weavr we're attached to
    weavr_name = models.CharField(max_length=200)
    weavr_url = models.CharField(max_length=200)
    
    # how did the last run of this guy go?
    last_run = models.DateTimeField(null=True)
    last_result = models.TextField(null=True)
    last_success = models.BooleanField(default=False)

    historical_results = models.TextField(null=True)
    
    # anything the prosthetic wants to store can go in here
    data = models.TextField(null=True,blank=True)

    def __unicode__(self):
        return self.oauth_key
        
    def get_json(self, url, params={}):
        token = oauth.OAuthToken(self.oauth_key, self.oauth_secret)
        try:
            return self.prosthetic.wrangler().get_json(token, url, params)
        except OAuthUnauthorizedException, e:
            logging.warn("token revoked!")
            self.revoked = True
            self.save()
            raise

    def post(self, url, params={}):
        token = oauth.OAuthToken(self.oauth_key, self.oauth_secret)
        try:
            return self.prosthetic.wrangler().post_json(token, url, params)
        except OAuthUnauthorizedException, e:
            logging.warn("token revoked!")
            self.revoked = True
            self.save()
            raise

    def blog_filter_url(self):
        if self.prosthetic.blog_keyword:
            return "%sfilter/~:%s"%( self.weavr_url, self.prosthetic.blog_keyword )
        return self.weavr_url

class RequestToken(models.Model):
    """An OAuth Request Token"""
    prosthetic = models.ForeignKey(Prosthetic)
    oauth_key = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.oauth_key
