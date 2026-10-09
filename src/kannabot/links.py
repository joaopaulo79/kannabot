"""Classify host policy without fetching links or following redirects."""
import ipaddress
import re
from urllib.parse import urlsplit

def normalize_host(host):
    if not isinstance(host,str) or not host:
        raise ValueError("Invalid host")
    host=host.rstrip(".").encode("idna").decode("ascii").lower()
    try:
        return ipaddress.ip_address(host).compressed
    except ValueError:
        pass
    labels=host.split(".")
    if len(host)>253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",label) for label in labels):
        raise ValueError("Invalid host")
    return host

def url_host(url):
    try:
        if not isinstance(url,str) or not url or any(char.isspace() for char in url):return None
        parsed=urlsplit(url if "://" in url else "https://"+url)
        if parsed.scheme.lower() not in ("http","https") or not parsed.hostname:return None
        if parsed.port is not None and not 1<=parsed.port<=65535:return None
        return normalize_host(parsed.hostname)
    except (ValueError,UnicodeError):
        return None

def extract_urls(message):
    urls=[]
    for text,entities in ((getattr(message,"text",None),getattr(message,"entities",None)),(getattr(message,"caption",None),getattr(message,"caption_entities",None))):
        text=text or ""
        urls.extend(match.group().rstrip(".,;!?:") for match in re.finditer(r"(?:https?://|www\.)[^\s<>()]+",text,re.IGNORECASE))
        encoded=text.encode("utf-16-le")
        for entity in entities or []:
            if entity.type=="text_link" and getattr(entity,"url",None):urls.append(entity.url)
            elif entity.type=="url":
                start,length=entity.offset,entity.length
                if type(start) is not int or type(length) is not int or start<0 or length<=0 or 2*(start+length)>len(encoded):continue
                try:urls.append(encoded[2*start:2*(start+length)].decode("utf-16-le"))
                except UnicodeError:continue
    return list(dict.fromkeys(urls))

def violates(message,options):
    def matches(host,domains):
        return any(host==domain or (options["include_subdomains"] and host.endswith("."+domain)) for domain in domains)
    for url in extract_urls(message):
        host=url_host(url)
        if host is None or matches(host,options["deny"]) or (options["allow"] and not matches(host,options["allow"])):
            return True
    return False
