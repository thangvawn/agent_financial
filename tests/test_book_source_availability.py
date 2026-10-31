import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from risk_dashboard.modules.learning.api import reader_proxy

BASE='/reader'
@pytest.fixture
def api(monkeypatch):
    app=FastAPI();app.include_router(reader_proxy.router)
    monkeypatch.setattr(reader_proxy,'_assert_public_host',lambda host: None)
    return TestClient(app)

def transport(monkeypatch,handler):
    original=httpx.Client
    monkeypatch.setattr(reader_proxy.httpx,'Client',lambda *args,**kwargs: original(*args,transport=httpx.MockTransport(handler),**kwargs))

def test_missing_download_has_honest_status_instead_of_html_success(api,monkeypatch):
    transport(monkeypatch,lambda req:httpx.Response(404))
    response=api.get(f'{BASE}/stream',params={'url':'https://www.gutenberg.org/missing.pdf'})
    assert response.status_code==404


def test_check_distinguishes_missing_and_temporary_errors(api,monkeypatch):
    transport(monkeypatch,lambda req:httpx.Response(404 if 'missing' in str(req.url) else 503))
    assert api.get(f'{BASE}/check',params={'url':'https://www.gutenberg.org/missing.pdf'}).json()['status']=='missing'
    assert api.get(f'{BASE}/check',params={'url':'https://www.gutenberg.org/busy.pdf'}).json()['status']=='unavailable'


def test_archive_uses_metadata_filename_and_excludes_private_files(api,monkeypatch):
    def handler(req):
        if '/metadata/' in str(req.url):
            return httpx.Response(200,json={'metadata':{'title':'Book'},'files':[{'name':'private.pdf','private':'true','size':'100'},{'name':'Actual Scan.pdf','format':'Text PDF','size':'100'}]})
        if req.url.path.endswith('Actual Scan.pdf'):
            return httpx.Response(206,headers={'content-type':'application/pdf'},content=b'%PDF-1.4\n'+b'x'*100)
        return httpx.Response(404)
    transport(monkeypatch,handler)
    result=api.get(f'{BASE}/check',params={'url':'https://archive.org/details/book-id'}).json()
    assert result.get('status')=='ready'
    assert result['resolved_url']=='https://archive.org/download/book-id/Actual%20Scan.pdf'
    assert result['kind']=='pdf'


def test_archive_restrictions_are_not_treated_as_missing_or_embedded(api,monkeypatch):
    transport(monkeypatch,lambda req:httpx.Response(200,json={'metadata':{'title':'Book','access-restricted-item':'true'},'files':[{'name':'book.pdf','private':'true'}]}))
    result=api.get(f'{BASE}/check',params={'url':'https://archive.org/details/borrow-book'}).json()
    assert result.get('status')=='restricted'
    assert not result.get('view_url')


def test_redirect_is_validated_before_requesting_next_host(api,monkeypatch):
    requested=[]
    def handler(req):
        requested.append(req.url.host)
        if req.url.host=='www.gutenberg.org':return httpx.Response(302,headers={'location':'http://127.0.0.1/private'})
        return httpx.Response(200,headers={'content-type':'application/pdf'},content=b'%PDF-1.4')
    transport(monkeypatch,handler)
    response=api.get(f'{BASE}/check',params={'url':'https://www.gutenberg.org/book.pdf'})
    assert requested==['www.gutenberg.org']
    assert response.status_code==400


def test_probe_reads_only_prefix_even_if_upstream_ignores_range(api,monkeypatch):
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            yield b'%PDF-1.4\n'+b'x'*1015
            raise AssertionError('Probe downloaded beyond the first 1024 bytes')
    transport(monkeypatch,lambda req:httpx.Response(200,headers={'content-type':'application/pdf'},stream=Body()))
    result=api.get(f'{BASE}/check',params={'url':'https://www.gutenberg.org/book.pdf'}).json()
    assert result.get('status')=='ready'
