#!/usr/bin/env python3
"""
AI Readers - API 集成测试
"""

import os
import time
import json
import tempfile
from pathlib import Path

import requests

# 配置
BASE_URL = "http://localhost:8086"
API_BASE = f"{BASE_URL}/api"


class TestAPI:
    """API 测试套件"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AI-Readers-Test/1.0"})
        self.created_projects = []
    
    def log(self, msg):
        print(f"[TEST] {msg}")
    
    def log_pass(self, msg):
        print(f"  ✅ {msg}")
    
    def log_fail(self, msg):
        print(f"  ❌ {msg}")
    
    # ========== 项目管理测试 ==========
    
    def test_list_projects(self):
        """测试获取项目列表"""
        self.log("测试 GET /api/projects")
        r = self.session.get(f"{API_BASE}/projects")
        assert r.status_code == 200, f"状态码: {r.status_code}"
        data = r.json()
        assert isinstance(data, list), "返回应为列表"
        self.log_pass(f"返回 {len(data)} 个项目")
        return data
    
    def test_create_project_text(self):
        """测试通过文本创建项目"""
        self.log("测试 POST /api/projects/json (文本)")
        payload = {
            "title": "测试文本项目",
            "article": "这是一篇测试文章。" * 100,
            "config": {
                "rounds": 2,
                "critics": ["结构批评者"],
                "defenders": ["平衡辩护者"]
            }
        }
        r = self.session.post(f"{API_BASE}/projects/json", json=payload)
        assert r.status_code == 200, f"状态码: {r.status_code}, 响应: {r.text}"
        data = r.json()
        assert "id" in data
        assert data["title"] == payload["title"]
        self.created_projects.append(data["id"])
        self.log_pass(f"项目ID: {data['id']}")
        return data["id"]
    
    def test_get_project(self, project_id):
        """测试获取单个项目"""
        self.log(f"测试 GET /api/projects/{project_id}")
        r = self.session.get(f"{API_BASE}/projects/{project_id}")
        assert r.status_code == 200, f"状态码: {r.status_code}"
        data = r.json()
        assert data["id"] == project_id
        self.log_pass(f"标题: {data['title']}")
        return data
    
    def test_delete_project(self, project_id):
        """测试删除项目"""
        self.log(f"测试 DELETE /api/projects/{project_id}")
        r = self.session.delete(f"{API_BASE}/projects/{project_id}")
        assert r.status_code == 200, f"状态码: {r.status_code}"
        self.log_pass("删除成功")
        
        # 验证已删除
        r = self.session.get(f"{API_BASE}/projects/{project_id}")
        # 项目不存在应返回错误
        self.log_pass("删除验证通过")
    
    # ========== 文件上传测试 ==========
    
    def test_upload_txt_file(self):
        """测试上传 TXT 文件"""
        self.log("测试 POST /api/projects (TXT文件)")
        
        # 创建临时 TXT 文件
        content = "这是测试内容。\n" * 1000
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            txt_path = f.name
        
        try:
            with open(txt_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {
                    'title': 'TXT文件测试',
                    'config': json.dumps({
                        "rounds": 2,
                        "critics": ["结构批评者"],
                        "defenders": ["平衡辩护者"]
                    })
                }
                r = self.session.post(f"{API_BASE}/projects", data=data, files=files)
            
            assert r.status_code == 200, f"状态码: {r.status_code}, 响应: {r.text}"
            result = r.json()
            assert "id" in result
            self.created_projects.append(result["id"])
            self.log_pass(f"上传成功，项目ID: {result['id']}")
            return result["id"]
        finally:
            os.unlink(txt_path)
    
    def test_upload_md_file(self):
        """测试上传 MD 文件"""
        self.log("测试 POST /api/projects (MD文件)")
        
        content = "# 测试标题\n\n这是测试内容。\n" * 500
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            md_path = f.name
        
        try:
            with open(md_path, 'rb') as f:
                files = {'file': ('test.md', f, 'text/markdown')}
                data = {
                    'title': 'Markdown文件测试',
                    'config': json.dumps({"rounds": 2, "critics": [], "defenders": []})
                }
                r = self.session.post(f"{API_BASE}/projects", data=data, files=files)
            
            assert r.status_code == 200, f"状态码: {r.status_code}"
            result = r.json()
            self.created_projects.append(result["id"])
            self.log_pass(f"上传成功，项目ID: {result['id']}")
            return result["id"]
        finally:
            os.unlink(md_path)
    
    def test_upload_large_txt_file(self):
        """测试上传大 TXT 文件（模拟大文件场景）"""
        self.log("测试 POST /api/projects (大TXT文件 - 5MB)")
        
        # 生成约 5MB 的文本文件
        content = "这是测试内容行。\n" * 50000  # 约 5MB
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            large_path = f.name
        
        try:
            file_size = os.path.getsize(large_path)
            self.log(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
            
            with open(large_path, 'rb') as f:
                files = {'file': ('large.txt', f, 'text/plain')}
                data = {
                    'title': '大文件测试',
                    'config': json.dumps({"rounds": 2, "critics": [], "defenders": []})
                }
                
                start = time.time()
                r = self.session.post(f"{API_BASE}/projects", data=data, files=files, timeout=300)
                elapsed = time.time() - start
            
            assert r.status_code == 200, f"状态码: {r.status_code}"
            result = r.json()
            self.created_projects.append(result["id"])
            self.log_pass(f"上传成功，耗时: {elapsed:.2f}s")
            return result["id"]
        finally:
            os.unlink(large_path)
    
    def test_upload_pdf_file(self):
        """测试上传 PDF 文件（模拟）"""
        self.log("测试 POST /api/projects (PDF文件 - 模拟)")
        
        # 注意：实际 PDF 需要二进制内容，这里用文本模拟
        # 真实测试需要提供实际的 PDF 文件
        content = b"%PDF-1.4\n" + b"x" * 1024 * 100  # 100KB 模拟
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(content)
            pdf_path = f.name
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': ('test.pdf', f, 'application/pdf')}
                data = {
                    'title': 'PDF文件测试',
                    'config': json.dumps({"rounds": 2, "critics": [], "defenders": []})
                }
                r = self.session.post(f"{API_BASE}/projects", data=data, files=files, timeout=300)
            
            assert r.status_code == 200, f"状态码: {r.status_code}"
            result = r.json()
            self.created_projects.append(result["id"])
            self.log_pass(f"上传成功，项目ID: {result['id']}")
            return result["id"]
        finally:
            os.unlink(pdf_path)
    
    def test_upload_real_pdf(self, pdf_path):
        """测试上传真实 PDF 文件"""
        self.log(f"测试 POST /api/projects (真实PDF: {pdf_path})")
        
        if not os.path.exists(pdf_path):
            self.log_fail(f"文件不存在: {pdf_path}")
            return None
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            data = {
                'title': os.path.basename(pdf_path),
                'config': json.dumps({"rounds": 2, "critics": ["结构批评者"], "defenders": ["平衡辩护者"]})
            }
            
            start = time.time()
            r = self.session.post(f"{API_BASE}/projects", data=data, files=files, timeout=300)
            elapsed = time.time() - start
        
        if r.status_code == 200:
            result = r.json()
            self.created_projects.append(result["id"])
            file_size = os.path.getsize(pdf_path)
            self.log_pass(f"上传成功 ({file_size/1024/1024:.2f}MB)，耗时: {elapsed:.2f}s")
            return result["id"]
        else:
            self.log_fail(f"上传失败: {r.status_code} - {r.text}")
            return None
    
    # ========== 边界测试 ==========
    
    def test_empty_title(self):
        """测试空标题"""
        self.log("测试空标题")
        payload = {
            "title": "",
            "article": "内容",
            "config": {"rounds": 2, "critics": [], "defenders": []}
        }
        r = self.session.post(f"{API_BASE}/projects/json", json=payload)
        # 应该返回错误
        self.log_pass(f"响应状态: {r.status_code}")
        return r.status_code != 200
    
    def test_empty_config(self):
        """测试空配置"""
        self.log("测试空配置")
        payload = {
            "title": "测试",
            "article": "内容",
            "config": {}
        }
        r = self.session.post(f"{API_BASE}/projects/json", json=payload)
        # 应该使用默认配置
        self.log_pass(f"响应状态: {r.status_code}")
        return r.status_code == 200
    
    def test_nonexistent_project(self):
        """测试获取不存在的项目"""
        self.log("测试获取不存在的项目")
        r = self.session.get(f"{API_BASE}/projects/nonexistent_id")
        self.log_pass(f"响应状态: {r.status_code}")
        return r.status_code == 404
    
    # ========== 清理 ==========
    
    def cleanup(self):
        """清理测试创建的项目"""
        self.log("清理测试项目...")
        for project_id in self.created_projects:
            try:
                self.session.delete(f"{API_BASE}/projects/{project_id}")
                self.log_pass(f"已删除: {project_id}")
            except:
                pass
    
    def run_all(self):
        """运行所有测试"""
        print("=" * 60)
        print("AI Readers API 测试套件")
        print("=" * 60)
        
        try:
            # 基础测试
            self.log("\n=== 基础功能测试 ===")
            self.test_list_projects()
            text_project_id = self.test_create_project_text()
            self.test_get_project(text_project_id)
            
            # 文件上传测试
            self.log("\n=== 文件上传测试 ===")
            self.test_upload_txt_file()
            self.test_upload_md_file()
            self.test_upload_large_txt_file()
            self.test_upload_pdf_file()
            
            # 边界测试
            self.log("\n=== 边界测试 ===")
            self.test_empty_title()
            self.test_empty_config()
            self.test_nonexistent_project()
            
            print("\n" + "=" * 60)
            print("✅ 所有测试通过!")
            print("=" * 60)
            
        except AssertionError as e:
            self.log_fail(f"测试失败: {e}")
            raise
        except Exception as e:
            self.log_fail(f"异常: {e}")
            raise
        finally:
            self.cleanup()


def main():
    """主函数"""
    tester = TestAPI()
    
    # 检查服务是否可用
    try:
        r = requests.get(BASE_URL, timeout=5)
        print(f"服务状态: {r.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print(f"请确保服务正在运行: {BASE_URL}")
        return
    
    # 运行测试
    tester.run_all()


if __name__ == "__main__":
    main()
