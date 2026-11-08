// Prints, as one JSON line, every role entry a SEHA user can pick: per tab
// (صحة طبي, صحة أعمال), per account (accordion), the entries "role - organization".
// Usage: node list-roles.mjs <baseUrl> <username> <password> <otp>
import { SEL, startSession } from "./lib.mjs";

const [, , baseUrl, username, password, otp = "1234"] = process.argv;
const out = { username, tabs: [] };
let browser;
try {
    const session = await startSession({ baseUrl, username, password, otp });
    browser = session.browser;
    const { page } = session;
    const tabCount = await page.locator(SEL.roleTab).count();
    for (let t = 0; t < Math.max(tabCount, 1); t++) {
        let tabName = "default";
        if (tabCount) {
            const tab = page.locator(SEL.roleTab).nth(t);
            await tab.click();
            await page.waitForTimeout(2500);
            tabName = (await tab.locator("img").getAttribute("alt")) ?? `tab-${t + 1}`;
        }
        const orgs = page.locator(SEL.roleOrg);
        const accounts = [];
        for (let i = 0; i < (await orgs.count()); i++) {
            const org = orgs.nth(i);
            const account = (await org.locator(SEL.roleOrgName).textContent()).trim();
            if (!((await org.getAttribute("class")) ?? "").includes("is-open")) {
                await org.locator(SEL.roleOrgHeader).click();
                await page.waitForTimeout(800);
            }
            const entries = (await org.locator(SEL.roleItemText).allTextContents()).map((x) => x.trim());
            accounts.push({ account, entries });
        }
        out.tabs.push({ tab: tabName, accounts });
    }
} catch (error) {
    out.error = String(error).split("\n")[0].slice(0, 300);
}
console.log(JSON.stringify(out));
if (browser) await browser.close();
