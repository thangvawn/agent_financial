import httpx
import pytest
from risk_dashboard.app.bootstrap.app_factory import create_app
from fastapi.testclient import TestClient
from risk_dashboard.modules.learning.api import reader_proxy

BASE='/api/v1/public/learning/reader'
@pytest.fixture
def api(monkeypatch):
    app=create_app()
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

@pytest.mark.parametrize('payload',[[],{'metadata':['invalid']},{'metadata':{'title':'x'},'files':42}])
def test_malformed_archive_metadata_does_not_crash(api,monkeypatch,payload):
    transport(monkeypatch,lambda req:httpx.Response(200,json=payload))
    result=api.get(f'{BASE}/check',params={'url':'https://archive.org/details/malformed'}).json()
    assert result['status']=='unavailable'

@pytest.mark.parametrize('code,status',[(410,'missing'),(401,'restricted'),(403,'restricted'),(451,'restricted'),(500,'unavailable')])
def test_upstream_status_classification(api,monkeypatch,code,status):
    transport(monkeypatch,lambda req:httpx.Response(code))
    assert api.get(f'{BASE}/check',params={'url':'https://gutenberg.org/a.pdf'}).json()['status']==status

@pytest.mark.parametrize('body,content_type,expected',[(b'<html>Error</html>','application/pdf','invalid'),(b'not a book','image/png','invalid'),(b'<html>Book</html>','text/html','ready'),(b'Book text','text/plain','ready'),(b'','application/pdf','invalid')])
def test_source_content_type_and_signature(api,monkeypatch,body,content_type,expected):
    transport(monkeypatch,lambda req:httpx.Response(200,content=body,headers={'content-type':content_type}))
    assert api.get(f'{BASE}/check',params={'url':'https://gutenberg.org/a'}).json()['status']==expected

@pytest.mark.parametrize('metadata,status',[({},'missing'),({'metadata':{'title':'No public copy'},'files':[{'name':'encrypted.pdf'},{'name':'private.pdf','private':'true'}]},'external')])
def test_missing_or_no_public_archive_copy(api,monkeypatch,metadata,status):
    transport(monkeypatch,lambda req:httpx.Response(200,json=metadata))
    assert api.get(f'{BASE}/check',params={'url':'https://archive.org/details/qa'}).json()['status']==status


def test_archive_uses_root_book_instead_of_page_fragments(api,monkeypatch):
    def handler(req):
        if '/metadata/' in str(req.url):
            return httpx.Response(200,json={'metadata':{'title':'Book'},'files':[{'name':'pages/001.pdf','format':'Text PDF'},{'name':'book_encrypted.pdf'},{'name':'full.pdf','size':'100','format':'Text PDF'}]})
        assert req.url.path.endswith('/full.pdf')
        return httpx.Response(200,content=b'%PDF-1.4\n%%EOF',headers={'content-type':'application/pdf'})
    transport(monkeypatch,handler)
    assert api.get(f'{BASE}/check',params={'url':'https://archive.org/details/qa'}).json()['status']=='ready'


def test_archive_text_fallback_for_oversized_pdf(api,monkeypatch):
    def handler(req):
        if '/metadata/' in str(req.url):
            return httpx.Response(200,json={'metadata':{'title':'Book'},'files':[{'name':'big.pdf','size':str(reader_proxy._MAX_BYTES+1)},{'name':'book_djvu.txt','size':'100'}]})
        assert req.url.path.endswith('book_djvu.txt')
        return httpx.Response(200,content=b'Book text',headers={'content-type':'text/plain'})
    transport(monkeypatch,handler)
    assert api.get(f'{BASE}/check',params={'url':'https://archive.org/details/qa'}).json()['kind']=='text'


def test_timeout_is_unavailable_not_missing(api,monkeypatch):
    def handler(req):raise httpx.ReadTimeout('timeout')
    transport(monkeypatch,handler)
    assert api.get(f'{BASE}/check',params={'url':'https://gutenberg.org/a.pdf'}).json()['status']=='unavailable'
    assert api.get(f'{BASE}/stream',params={'url':'https://gutenberg.org/a.pdf'}).status_code==502


def test_stream_pdf_success_and_size_limit(api,monkeypatch):
    def handler(req):
        size=reader_proxy._MAX_BYTES+1 if 'huge' in str(req.url) else 14
        return httpx.Response(200,content=b'%PDF-1.4\n%%EOF',headers={'content-type':'application/pdf','content-length':str(size)})
    transport(monkeypatch,handler)
    response=api.get(f'{BASE}/stream',params={'url':'https://gutenberg.org/a.pdf'})
    assert response.status_code==200 and response.content==b'%PDF-1.4\n%%EOF'
    assert api.get(f'{BASE}/stream',params={'url':'https://gutenberg.org/huge.pdf'}).status_code==413
    assert api.get(f'{BASE}/check',params={'url':'https://gutenberg.org/huge.pdf'}).json()['status']=='too_large'


@pytest.mark.parametrize('url',['http://127.0.0.1/book.pdf','https://gutenberg.org.evil.test/book.pdf','https://user:pass@gutenberg.org/book.pdf','https://gutenberg.org:999/book.pdf','ftp://gutenberg.org/book.pdf'])
def test_rejects_unsafe_targets(api,url):
    assert api.get(f'{BASE}/check',params={'url':url}).status_code==400


def test_redirect_loop_is_bounded(api,monkeypatch):
    requests=[]
    def handler(req):
        requests.append(req)
        return httpx.Response(302,headers={'location':'/loop.pdf'})
    transport(monkeypatch,handler)
    assert api.get(f'{BASE}/check',params={'url':'https://gutenberg.org/loop.pdf'}).status_code==502
    assert len(requests)==5


def test_archive_collection_with_multiple_unrelated_books_is_not_mislabelled(api,monkeypatch):
    transport(monkeypatch,lambda req:httpx.Response(200,json={'metadata':{'title':'Finance collection'},'files':[{'name':'A-Different-Book.pdf','format':'Text PDF'},{'name':'Financial-Reporting.pdf','format':'Text PDF'}]}))
    result=api.get(f'{BASE}/check',params={'url':'https://archive.org/details/finance-collection'}).json()
    assert result['status']=='external'
    assert not result.get('view_url')
