#!/usr/bin/env node
// Standalone, non-interactive Playwright driver that logs into SEHA as a given
// user profile and prints the resulting app token to stdout. Ported from the
// headed, UI-driven flow in seha-login-test-flow (flows.config.ts + lib/playwright-engine.ts),
// with all interactivity removed and headless as the default. This script never
// asks questions and never writes to any project's env files or caches — the
// caller (the seha-auth skill) is responsible for all of that.

import { chromium } from "playwright";

// A selector value that's an array means "try this one, or that one" — every
// candidate is combined into a single locator (see buildLocator) so whichever
// one is actually present in the DOM wins. Kept in sync with the OR-fallback
// selectors in the sibling seha-login-test-flow project's flows.config.ts —
// when SEHA ships a UI redesign that breaks a selector there, the fix (old
// selector kept, new one added alongside it) should be ported here too.
const FIXED_SELECTORS = {
    usernameInput: 'input[data-testid="username-input"]',
    passwordInput: 'input[data-testid="password-input"]',
    loginButton: 'button[data-testid="username-password-login-button"]',
    // Legacy layout's absolute path, OR the icon-based selector that survived
    // the 2026 redesign's extra layout wrapper div.
    logoutLink: [
        "#root > div > section > section > header > div > div.nav-icons > div > span:nth-child(3) > a",
        'a:has(svg[data-icon="arrow-right-from-bracket"])'
    ],
    logoutConfirm: "button.swal2-confirm.btn.btn-primary.ms-1",
    logoutDismiss: "button.swal2-confirm.swal2-styled",
    otpModalOpenButton:
        "body > div.fade.modal.show > div > div > div.modal-body > div > div > button:nth-child(1)",
    // Redesigned UI only: the OTP field is disabled until a delivery method
    // is picked, so pick SMS. :not([disabled]) keeps this a no-op on the
    // custom login page (SMS disabled there, email pre-selected and already
    // sent) and on the legacy UI (button doesn't exist at all).
    otpDeliveryMethodSms: 'button.otp-switcher__item:not([disabled]):has-text("رسالة نصية")',
    otpInput: [
        'input[placeholder="ادخل رمز التحقق"]', // legacy UI
        "input.otp-field__input" // redesigned UI (2026)
    ],
    otpSubmitButton: [
        'form:has(input[placeholder="ادخل رمز التحقق"]) button[type="submit"]', // legacy UI
        'form.otp-field button[type="submit"]' // redesigned UI (2026)
    ],
    businessTab: [
        '.ant-tabs-tab[data-node-key="2"]', // legacy UI
        'button.role-tab:has(img[alt="صحة أعمال"])' // redesigned UI (2026)
    ],
    // Legacy layout's absolute path, OR the class-based selector that
    // survived the 2026 redesign's extra layout wrapper div.
    servicesMenuTrigger: [
        "#root > div > section > aside > div > div.menu-container > ul > li.ant-menu-submenu.ant-menu-submenu-vertical > div",
        "li.ant-menu-submenu.ant-menu-submenu-vertical > .ant-menu-submenu-title"
    ],
    servicesSubmenuPopup: ".ant-menu-submenu-popup:not(.ant-menu-submenu-hidden)",
    strayModalDismissButton: ".ant-modal-wrap .ant-modal-content .ant-modal-footer > button"
};

function buildLocator(page, selector) {
    const candidates = Array.isArray(selector) ? selector : [selector];
    return candidates
        .map((s) => page.locator(s))
        .reduce((combined, next) => combined.or(next));
}

function parseArgs(argv) {
    const args = {};
    for (let i = 0; i < argv.length; i++) {
        const raw = argv[i];
        if (!raw.startsWith("--")) continue;
        const key = raw.slice(2);
        if (key === "is-business" || key === "headed") {
            args[key] = true;
            continue;
        }
        args[key] = argv[i + 1];
        i++;
    }
    return args;
}

async function clickWithFallback(page, selector, timeout = 15000) {
    const locator = buildLocator(page, selector).first();
    try {
        await locator.click({ timeout });
    } catch {
        await locator.dispatchEvent("click");
    }
}

async function dismissIfVisible(page, selector, timeout = 3000) {
    const locator = buildLocator(page, selector).first();
    try {
        await locator.waitFor({ state: "visible", timeout });
        await locator.click({ timeout: 3000 });
    } catch {
        // not present, or present but not actionable (e.g. disabled) — continue
    }
}

const KNOWN_LOGIN_PATHS = ["/#/Account/Login", "/#/Account/custom-Login"];

async function resolveWorkingLoginPath(page, sehaBaseUrl, preferredPath) {
    const ordered = [
        preferredPath,
        ...KNOWN_LOGIN_PATHS.filter((path) => path !== preferredPath)
    ];

    for (const path of ordered) {
        const url = `${sehaBaseUrl.replace(/\/$/, "")}${path}`;
        await page.goto(url, { waitUntil: "domcontentloaded" });

        const foundLoginForm = await page
            .waitForSelector(FIXED_SELECTORS.usernameInput, { timeout: 8000 })
            .then(() => true)
            .catch(() => false);

        if (foundLoginForm) {
            return { path, url };
        }
    }

    throw new Error(
        `Could not find the username input at any known login path (tried: ${ordered.join(", ")}). SEHA's login page structure may have changed.`
    );
}

async function logoutIfAlreadyLoggedIn(page, loginUrl) {
    const alreadyLoggedIn = await buildLocator(page, FIXED_SELECTORS.logoutLink)
        .first()
        .waitFor({ state: "visible", timeout: 5000 })
        .then(() => true)
        .catch(() => false);

    if (!alreadyLoggedIn) return;

    await clickWithFallback(page, FIXED_SELECTORS.logoutLink);
    await dismissIfVisible(page, FIXED_SELECTORS.logoutConfirm);
    await dismissIfVisible(page, FIXED_SELECTORS.logoutDismiss);
    await page.goto(loginUrl, { waitUntil: "domcontentloaded" });
}

async function login(page, username, password) {
    await page.fill(FIXED_SELECTORS.usernameInput, username, { timeout: 15000 });
    await page.fill(FIXED_SELECTORS.passwordInput, password, { timeout: 15000 });
    await clickWithFallback(page, FIXED_SELECTORS.loginButton);
}

async function handleOtp(page, otp) {
    await dismissIfVisible(page, FIXED_SELECTORS.otpModalOpenButton);
    // Redesigned UI only: picks SMS as the delivery method, which unlocks the
    // (until then disabled) OTP field. No-op everywhere else — see the
    // comment on otpDeliveryMethodSms above.
    await dismissIfVisible(page, FIXED_SELECTORS.otpDeliveryMethodSms);
    await buildLocator(page, FIXED_SELECTORS.otpInput)
        .first()
        .fill(otp, { timeout: 15000 });
    await clickWithFallback(page, FIXED_SELECTORS.otpSubmitButton);
}

async function selectBusinessTabIfNeeded(page, isBusiness) {
    if (!isBusiness) return;
    await clickWithFallback(page, FIXED_SELECTORS.businessTab);
}

async function selectFromAccordion(page, accordionName, accountName) {
    const accordionSelector = `text=${accordionName}`;
    const accountSelector = `text=${accountName}`;

    const accordions = page.locator(accordionSelector);
    await accordions.first().waitFor({ state: "visible", timeout: 15000 });
    const count = await accordions.count();

    const visibleAccount = () =>
        page.locator(accountSelector).filter({ visible: true }).first();

    for (let i = 0; i < count; i++) {
        if (await visibleAccount().isVisible()) {
            await visibleAccount().click();
            return;
        }

        await accordions.nth(i).click();
        try {
            const account = visibleAccount();
            await account.waitFor({ state: "visible", timeout: 3000 });
            await account.click();
            return;
        } catch {
            await accordions.nth(i).click();
        }
    }

    throw new Error(
        `Account "${accountName}" not found in any of ${count} accordion(s) matching "${accordionName}"`
    );
}

async function selectService(page, serviceName) {
    await dismissIfVisible(page, FIXED_SELECTORS.strayModalDismissButton);

    await buildLocator(page, FIXED_SELECTORS.servicesMenuTrigger)
        .first()
        .hover({ timeout: 15000 });
    await page.waitForSelector(FIXED_SELECTORS.servicesSubmenuPopup, { timeout: 15000 });

    const strayModalDismissed = await dismissIfVisible(
        page,
        FIXED_SELECTORS.strayModalDismissButton
    ).then(() => true);
    if (strayModalDismissed) {
        await page.waitForTimeout(500);
        await buildLocator(page, FIXED_SELECTORS.servicesMenuTrigger)
            .first()
            .hover({ timeout: 15000 });
        await page.waitForSelector(FIXED_SELECTORS.servicesSubmenuPopup, { timeout: 15000 });
    }

    const serviceItemSelector = `${FIXED_SELECTORS.servicesSubmenuPopup} .ant-menu-item:has-text('${serviceName}')`;
    const serviceItem = page.locator(serviceItemSelector).first();
    const found = await serviceItem
        .waitFor({ state: "visible", timeout: 5000 })
        .then(() => true)
        .catch(() => false);

    if (!found) {
        const availableServices = await page
            .locator(`${FIXED_SELECTORS.servicesSubmenuPopup} .ant-menu-item`)
            .allTextContents()
            .catch(() => []);
        // Distinct, greppable message: not every role's menu has the same
        // services, so this is a "wrong service name for this role" signal,
        // not a generic selector-breakage signal — the skill asks the user
        // for the right name instead of surfacing this as an opaque error.
        throw new Error(
            `Service "${serviceName}" not found in the services menu for this role. Available services: [${availableServices.join(", ")}]`
        );
    }

    await clickWithFallback(page, serviceItemSelector);
}

async function extractTokenFromIframe(page, iframePattern) {
    const iframeSelector = `iframe[src*="${iframePattern}"]`;
    await page.waitForSelector(iframeSelector, { timeout: 30000 });

    const iframeHandle = await page.$(iframeSelector);
    if (!iframeHandle) {
        throw new Error(`Could not find iframe matching "${iframePattern}"`);
    }

    const frame = await iframeHandle.contentFrame();
    if (!frame) {
        throw new Error(`Could not access content frame for iframe matching "${iframePattern}"`);
    }

    await frame.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(3000);

    const maxAttempts = 10;
    const intervalMs = 2000;
    let lastRaw = "";

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        const raw = await frame.evaluate(() => localStorage.getItem("persist:auth") ?? "");
        lastRaw = raw;

        if (raw) {
            try {
                const parsed = JSON.parse(raw);
                let value = parsed.token;
                if (value === undefined || value === null) {
                    throw new Error(
                        `Key "token" not found in parsed persist:auth. Available keys: [${Object.keys(parsed).join(", ")}]`
                    );
                }
                if (typeof value === "string" && value.startsWith('"')) {
                    value = JSON.parse(value);
                }
                if (value) return value;
            } catch (e) {
                if (attempt === maxAttempts) throw e;
            }
        }

        if (attempt < maxAttempts) {
            await new Promise((r) => setTimeout(r, intervalMs));
        }
    }

    throw new Error(
        `Token not found after ${maxAttempts} attempts (${(maxAttempts * intervalMs) / 1000}s). Final raw persist:auth (first 500 chars): ${lastRaw.slice(0, 500) || "(empty)"}`
    );
}

async function main() {
    const args = parseArgs(process.argv.slice(2));

    const required = [
        "seha-base-url",
        "login-path",
        "username",
        "password",
        "accordion-name",
        "account-name",
        "service-name",
        "iframe-pattern"
    ];
    const missing = required.filter((key) => !args[key]);
    if (missing.length > 0) {
        console.error(`Missing required arguments: ${missing.map((k) => `--${k}`).join(", ")}`);
        process.exit(2);
    }

    const otp = args.otp ?? "1234";
    const headless = !args.headed;

    const debugDir = args["debug-dir"];
    const snap = async (label) => {
        if (!debugDir) return;
        try {
            await page.screenshot({ path: `${debugDir}/${label}.png`, fullPage: true });
        } catch {
            // best-effort only, never let debug capture break the real flow
        }
    };

    let browser;
    let page;
    try {
        browser = await chromium.launch({ headless });
        const context = await browser.newContext({ viewport: null });
        page = await context.newPage();

        const { path: workingLoginPath, url: loginUrl } = await resolveWorkingLoginPath(
            page,
            args["seha-base-url"],
            args["login-path"]
        );
        await snap("01-login-page");
        await logoutIfAlreadyLoggedIn(page, loginUrl);

        await login(page, args.username, args.password);
        await snap("02-after-login-submit");
        await handleOtp(page, otp);
        await snap("03-after-otp-submit");
        await selectBusinessTabIfNeeded(page, Boolean(args["is-business"]));
        await snap("04-after-business-tab");
        await selectFromAccordion(page, args["accordion-name"], args["account-name"]);
        await snap("05-after-accordion");
        await selectService(page, args["service-name"]);
        await snap("06-after-service-select");

        const token = await extractTokenFromIframe(page, args["iframe-pattern"]);

        console.log(`TOKEN=${token}`);
        console.log(`LOGIN_PATH=${workingLoginPath}`);
        process.exit(0);
    } catch (error) {
        if (page) await snap("99-error");
        console.error(`ERROR=${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    } finally {
        if (browser) await browser.close();
    }
}

main();
