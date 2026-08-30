"""
Pastefy API Uploader
Загружает обфусцированный код на pastefy.app
Работает с API ключом и без него (анонимно)
"""

import aiohttp
import os

PASTEFY_API_KEY = os.getenv('PASTEFY_API_KEY')
PASTEFY_BASE_URL = "https://pastefy.app/api/v2"


class PastefyUploader:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or PASTEFY_API_KEY
        self.session = None
    
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def upload_paste(
        self,
        title: str,
        content: str,
        visibility: str = "UNLISTED",
        encrypted: bool = False
    ) -> dict:
        """
        Загружает пасту на Pastefy
        БЕЗ API ключа: только PUBLIC или UNLISTED
        С API ключом: можно и PRIVATE
        """
        url = f"{PASTEFY_BASE_URL}/paste"
        
        payload = {
            "title": title,
            "content": content,
            "visibility": visibility,
            "encrypted": encrypted
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            if visibility == "PRIVATE":
                visibility = "UNLISTED"
                payload["visibility"] = "UNLISTED"
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                
                if resp.status in (200, 201):
                    paste_id = data.get("paste", {}).get("id") or data.get("id")
                    return {
                        "success": True,
                        "id": paste_id,
                        "url": f"https://pastefy.app/{paste_id}",
                        "raw_url": f"https://pastefy.app/{paste_id}/raw",
                        "title": data.get("paste", {}).get("title", title),
                        "visibility": visibility,
                        "anonymous": not bool(self.api_key)
                    }
                else:
                    if self.api_key and resp.status in (401, 403):
                        return await self._upload_anonymous(title, content, visibility, encrypted)
                    
                    return {
                        "success": False,
                        "error": data.get("message", f"HTTP {resp.status}"),
                        "details": data
                    }
                    
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def _upload_anonymous(self, title, content, visibility, encrypted):
        """Fallback: загрузка без API ключа"""
        url = f"{PASTEFY_BASE_URL}/paste"
        
        if visibility == "PRIVATE":
            visibility = "UNLISTED"
        
        payload = {
            "title": title,
            "content": content,
            "visibility": visibility,
            "encrypted": encrypted
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload, headers={
                "Content-Type": "application/json"
            }) as resp:
                data = await resp.json()
                
                if resp.status in (200, 201):
                    paste_id = data.get("paste", {}).get("id") or data.get("id")
                    return {
                        "success": True,
                        "id": paste_id,
                        "url": f"https://pastefy.app/{paste_id}",
                        "raw_url": f"https://pastefy.app/{paste_id}/raw",
                        "title": title,
                        "visibility": visibility,
                        "anonymous": True,
                        "note": "Загружено анонимно (без API ключа)"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Anonymous upload failed: {data.get('message', f'HTTP {resp.status}')}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Anonymous upload error: {str(e)}"
            }
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
