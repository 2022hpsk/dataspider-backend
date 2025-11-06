from playwright.async_api import BrowserContext, Page


class RednoteLogin:
    def __init__(
        self,
        browser_context: BrowserContext,
        context_page: Page,
        login_state_path: str,
    ):
        self.browser_context = browser_context
        self.context_page = context_page
        self.login_state_path = login_state_path

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            await self.context_page.wait_for_selector("img.reds-img", timeout=180000)
            return True
        except:
            return False

    async def click_login_button(self):
        """点击登录按钮，进行手动登录"""
        await self.context_page.goto(
            "https://www.xiaohongshu.com/", wait_until="domcontentloaded"
        )
        await self.context_page.locator(
            "button.login-btn:has-text('登录')"
        ).first.click()

        print("请在浏览器中完成登录（验证码 / 扫码）...")
