// Selects one role entry, checks the service is in the services menu, and reads
// SEHA's own token for that role from the Authorization header of SEHA's API
// calls (not the token SEHA puts in the app iframe, which only reaches the app
// once the app's backend is deployed). Prints one JSON line with the decoded
// claims (never the raw token).
// Usage: node role-token.mjs <baseUrl> <username> <password> <otp> <tab> <account> <entry> <serviceName>
//        [--app-host <host> [--app-storage-key persist:auth] [--app-token-field token]]
// With --app-host (app mode), it also opens the service and reads the app's own token from the app iframe's
// localStorage (the key the app persists its auth state under), once the app has exchanged SEHA's token.
import { SEL, decodeJwt, loc, normalizeArabic, startSession, tryClick } from "./lib.mjs";

const [, , baseUrl, username, password, otp, tab, account, entry, serviceName, ...flags] = process.argv;
const flag = (name, fallback) => { const i = flags.indexOf(`--${name}`); return i >= 0 ? flags[i + 1] : fallback; };
const appHost = flag("app-host", "");
const appStorageKey = flag("app-storage-key", "persist:auth");
const appTokenField = flag("app-token-field", "token");
const out = { username, tab, account, entry };
const bearerTokens = [];
let browser;
let selected = false;
try {
    const session = await startSession({ baseUrl, username, password, otp });
    browser = session.browser;
    const { page } = session;
    const sehaHost = new URL(baseUrl).host;
    page.on("request", (request) => {
        const header = request.headers()["authorization"];
        if (selected && header?.startsWith("Bearer ey") && request.url().includes(sehaHost)) {
            bearerTokens.push(header.slice(7));
        }
    });
    if ((await page.locator(SEL.roleTab).count()) > 1) {
        await page.locator(`${SEL.roleTab}:has(img[alt="${tab}"])`).click();
        await page.waitForTimeout(2500);
    }
    const org = page
        .locator(SEL.roleOrg)
        .filter({ has: page.locator(SEL.roleOrgName, { hasText: account.trim() }) })
        .first();
    await org.waitFor({ timeout: 30000 });
    if (!((await org.getAttribute("class")) ?? "").includes("is-open")) {
        await org.locator(SEL.roleOrgHeader).click();
        await page.waitForTimeout(800);
    }
    const item = org
        .locator(SEL.roleItem)
        .filter({ has: page.locator(SEL.roleItemText, { hasText: entry.trim() }) })
        .first();
    selected = true;
    await item.click({ timeout: 30000 });
    await tryClick(page, SEL.strayModal);
    await loc(page, SEL.servicesTrigger).first().hover({ timeout: 45000 });
    await page.waitForSelector(SEL.servicesPopup, { timeout: 15000 });
    if (await tryClick(page, SEL.strayModal)) {
        await page.waitForTimeout(500);
        await loc(page, SEL.servicesTrigger).first().hover({ timeout: 15000 });
        await page.waitForSelector(SEL.servicesPopup, { timeout: 15000 });
    }
    out.services = (await page.locator(`${SEL.servicesPopup} .ant-menu-item`).allTextContents())
        .map((x) => x.trim())
        .filter(Boolean);
    const wanted = normalizeArabic(serviceName);
    out.serviceFound =
        out.services.find((s) => normalizeArabic(s) === wanted) ??
        out.services.find((s) => normalizeArabic(s).includes(wanted) || wanted.includes(normalizeArabic(s))) ??
        null;
    await page.waitForTimeout(2000);
    const stored = await page.evaluate(() => {
        const found = [];
        for (const store of [localStorage, sessionStorage]) {
            for (let i = 0; i < store.length; i++) {
                const value = store.getItem(store.key(i)) ?? "";
                found.push(...(value.match(/ey[\w-]+\.[\w-]+\.[\w-]+/g) ?? []));
            }
        }
        return found;
    });
    const claims = [...bearerTokens, ...stored].map(decodeJwt).filter(Boolean);
    const withPermissions = claims.filter((c) => "PermissionList" in c);
    const chosen = withPermissions.at(-1) ?? claims.at(-1);
    if (!chosen) throw new Error("no SEHA token found after selecting the role");
    out.claims = Object.fromEntries(Object.entries(chosen).filter(([key]) => !/secret|password|token|hmac/i.test(key)));
    out.tokenReceived = true;
    if (appHost && out.serviceFound) {
        await page.locator(`${SEL.servicesPopup} .ant-menu-item`).filter({ hasText: out.serviceFound }).first().click();
        const iframe = page.locator(`iframe[src*="${appHost}"]`).first();
        await iframe.waitFor({ state: "attached", timeout: 45000 });
        const frame = await (await iframe.elementHandle()).contentFrame();
        let appToken = null;
        for (let attempt = 0; attempt < 15 && !appToken; attempt++) {
            await page.waitForTimeout(2000);
            const raw = await frame.evaluate((key) => localStorage.getItem(key) ?? "", appStorageKey).catch(() => "");
            try {
                const parsed = JSON.parse(raw);
                let value = parsed?.[appTokenField];
                if (typeof value === "string" && value.startsWith('"')) value = JSON.parse(value);
                if (value) appToken = value;
            } catch {
                if (/^ey[\w-]+\.[\w-]+\.[\w-]+$/.test(raw)) appToken = raw;
            }
        }
        const appClaims = appToken ? decodeJwt(appToken) : null;
        if (appClaims) {
            out.appClaims = Object.fromEntries(Object.entries(appClaims).filter(([key]) => !/secret|password|token|hmac/i.test(key)));
            out.appTokenReceived = true;
        } else {
            out.appError = `no app token under localStorage "${appStorageKey}" in the ${appHost} iframe after 30 s`;
        }
    }
} catch (error) {
    out.error = String(error).split("\n")[0].slice(0, 300);
}
console.log(JSON.stringify(out));
if (browser) await browser.close();
