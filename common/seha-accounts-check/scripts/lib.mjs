// Shared SEHA login helpers for the seha-accounts-check scripts. Playwright comes
// from the seha-auth skill's own install (run its Step 1 once), so this skill adds
// no dependency of its own.
import { createRequire } from "module";
import { fileURLToPath } from "url";
import path from "path";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(here, "../../seha-auth/scripts/package.json"));
export const { chromium } = require("playwright");

export const SEL = {
    user: 'input[data-testid="username-input"]',
    pass: 'input[data-testid="password-input"]',
    login: 'button[data-testid="username-password-login-button"]',
    otpOpen: "body > div.fade.modal.show > div > div > div.modal-body > div > div > button:nth-child(1)",
    otpSms: 'button.otp-switcher__item:not([disabled]):has-text("رسالة نصية")',
    otpInput: ['input[placeholder="ادخل رمز التحقق"]', "input.otp-field__input"],
    otpSubmit: [
        'form:has(input[placeholder="ادخل رمز التحقق"]) button[type="submit"]',
        'form.otp-field button[type="submit"]'
    ],
    roleTab: "button.role-tab",
    roleOrg: ".role-org",
    roleOrgHeader: ".role-org__header",
    roleOrgName: ".role-org__name",
    roleItem: ".role-item",
    roleItemText: ".role-item__text",
    servicesTrigger: [
        "#root > div > section > aside > div > div.menu-container > ul > li.ant-menu-submenu.ant-menu-submenu-vertical > div",
        "li.ant-menu-submenu.ant-menu-submenu-vertical > .ant-menu-submenu-title"
    ],
    servicesPopup: ".ant-menu-submenu-popup:not(.ant-menu-submenu-hidden)",
    strayModal: ".ant-modal-wrap .ant-modal-content .ant-modal-footer > button"
};

export const loc = (page, s) =>
    (Array.isArray(s) ? s : [s]).map((x) => page.locator(x)).reduce((a, b) => a.or(b));

export async function tryClick(page, s, timeout = 3000) {
    try {
        const l = loc(page, s).first();
        await l.waitFor({ state: "visible", timeout });
        await l.click({ timeout: 3000 });
        return true;
    } catch {
        return false;
    }
}

// Arabic-insensitive comparison: service and role names differ in hamza, alef
// maqsura, taa marbuta and spacing between environments and sheets.
export const normalizeArabic = (s) =>
    String(s)
        .replace(/[ً-ْـ]/g, "")
        .replace(/[أإآ]/g, "ا")
        .replace(/ى/g, "ي")
        .replace(/ة/g, "ه")
        .replace(/\s+/g, " ")
        .trim();

export function decodeJwt(token) {
    try {
        const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(Buffer.from(part, "base64").toString("utf8"));
    } catch {
        return null;
    }
}

// Logs in and lands on the role selection page. The 6 s pause before submitting
// is required: SEHA loads an invisible reCAPTCHA that scores the session, and a
// login submitted before it is ready never leaves the spinner.
export async function startSession({ baseUrl, username, password, otp }) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: null });
    const page = await context.newPage();
    let found = false;
    for (const loginPath of ["/#/Account/Login", "/#/Account/custom-Login"]) {
        await page.goto(baseUrl.replace(/\/$/, "") + loginPath, { waitUntil: "domcontentloaded", timeout: 90000 });
        found = await page
            .waitForSelector(SEL.user, { timeout: 20000 })
            .then(() => true)
            .catch(() => false);
        if (found) break;
    }
    if (!found) throw new Error("SEHA login form not found on either login page");
    await page.waitForTimeout(6000);
    await page.fill(SEL.user, username, { timeout: 15000 });
    await page.fill(SEL.pass, password, { timeout: 15000 });
    const loginButton = page.locator(SEL.login).first();
    try {
        await loginButton.click({ timeout: 15000 });
    } catch {
        await loginButton.dispatchEvent("click");
    }
    await tryClick(page, SEL.otpOpen);
    await tryClick(page, SEL.otpSms);
    await loc(page, SEL.otpInput).first().fill(otp, { timeout: 45000 });
    const submit = loc(page, SEL.otpSubmit).first();
    try {
        await submit.click({ timeout: 15000 });
    } catch {
        await submit.dispatchEvent("click");
    }
    await page.waitForSelector(SEL.roleOrgHeader, { timeout: 60000 });
    return { browser, page };
}
