import { expect, test } from "@playwright/test"

const API_BASE = "http://127.0.0.1:18086"
const PASSWORD = "DemoPass123!"
const OTHER_AGENCY_ID = "browser-acceptance-other-agency"
const OFFER_WORKSPACE_ID = "browser-acceptance-offer"
const REQUESTED_DOCUMENT_ID = "browser-acceptance-requested-document"
const INTERNAL_SENTINEL = "BROWSER-INTERNAL-SENTINEL"

async function signIn(page, email, expectedPath) {
  await page.goto("/login")
  await page.evaluate(() => window.localStorage.clear())
  await page.reload()
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill(PASSWORD)
  await page.getByRole("button", { name: "Sign in", exact: true }).click()
  await page.waitForURL((url) => url.pathname === expectedPath)
}

async function browserApi(page, method, path, body) {
  return page.evaluate(
    async ({ apiBase, methodName, requestPath, requestBody }) => {
      const session = JSON.parse(
        window.localStorage.getItem("aeroassist.authSession") || "{}",
      )
      const response = await fetch(`${apiBase}${requestPath}`, {
        method: methodName,
        headers: {
          "Content-Type": "application/json",
          ...(session.access_token
            ? {
                Authorization: `${session.token_type || "bearer"} ${session.access_token}`,
              }
            : {}),
        },
        body:
          requestBody === undefined ? undefined : JSON.stringify(requestBody),
      })
      const payload = await response.json().catch(() => ({}))
      return {
        ok: response.ok,
        status: response.status,
        body: payload,
      }
    },
    {
      apiBase: API_BASE,
      methodName: method,
      requestPath: path,
      requestBody: body,
    },
  )
}

async function selectFirstRealOption(locator) {
  await expect(locator).toBeEnabled()
  await expect
    .poll(async () =>
      locator.locator("option").evaluateAll((options) =>
        options.filter((option) => option.value && !option.value.startsWith("legacy:")).length,
      ),
    )
    .toBeGreaterThan(0)
  const value = await locator.locator("option").evaluateAll((options) =>
    options.find((option) => option.value && !option.value.startsWith("legacy:"))?.value,
  )
  await locator.selectOption(value)
  return value
}

async function fillReferenceAutocomplete(locator, value) {
  await expect
    .poll(async () =>
      locator.evaluate((element) => {
        const list = document.getElementById(element.getAttribute("aria-controls"))
        return list?.querySelectorAll("option").length || 0
      }),
    )
    .toBeGreaterThan(0)
  await locator.fill(value)
  await expect(locator).toHaveValue(value)
  await locator.blur()
}

function currentPathId(page) {
  return new URL(page.url()).pathname.split("/").filter(Boolean).pop()
}

test("canonical Product Recovery browser acceptance", async ({ page }) => {
  test.setTimeout(300_000)
  const pageErrors = []
  page.on("pageerror", (error) => pageErrors.push(error.message))

  let agencyId = ""
  let requestId = ""
  let deliveryId = ""
  let tripId = ""
  let bookingWorkspaceId = ""
  let ticketId = ""
  let emdId = ""
  let invoiceId = ""
  let invoiceNumber = ""

  await test.step("01 Platform Owner can sign in", async () => {
    await signIn(page, "owner@aeroassist.dev", "/platform")
    await expect(page.getByRole("main")).toBeVisible()
  })

  await test.step("02 Platform overview loads", async () => {
    await expect(page.getByText(/Platform Overview|Platform Console/i).first()).toBeVisible()
  })

  await test.step("03 Platform Agency list loads", async () => {
    await page.goto("/platform/agencies")
    await expect(page.getByRole("heading", { name: /Agencies/i }).first()).toBeVisible()
    await expect(page.getByText("Demo AeroAssist Travel", { exact: true }).first()).toBeVisible()
  })

  await test.step("04 Agency Owner can sign in", async () => {
    await signIn(page, "agency.owner@aeroassist.dev", "/agency")
    const me = await browserApi(page, "GET", "/api/auth/me")
    expect(me.status).toBe(200)
    agencyId =
      me.body.authorization?.agency_memberships?.[0]?.membership?.agency_id ||
      me.body.memberships?.[0]?.agency_id
    expect(agencyId).toBeTruthy()
  })

  await test.step("05 Operations Command Centre loads", async () => {
    await expect(
      page.getByRole("heading", { name: "Dashboard", exact: true }).first(),
    ).toBeVisible()
    await expect(page.getByText(/Today.s work/, { exact: true })).toBeVisible()
  })

  await test.step("06 Request V4 creation surface loads", async () => {
    await page.goto("/agency/requests/new")
    await expect(
      page.getByRole("heading", { name: "New travel request" }),
    ).toBeVisible()
  })

  await test.step("07 Existing Client is selected", async () => {
    const client = page.locator("#builder-1 select").first()
    await expect(client).toBeEnabled()
    await client.selectOption({ label: "Anna Novak" })
  })

  await test.step("08 Existing Passenger is selected", async () => {
    await page.locator("#builder-3 select").nth(0).selectOption({ label: "Anna Novak" })
  })

  await test.step("09 Reference-driven PTC is selected", async () => {
    const ptc = page.locator("#builder-3 select").nth(1)
    await expect(ptc).toBeEnabled()
    await ptc.selectOption({ label: "ADT - Adult" })
  })

  await test.step("10 First canonical itinerary segment is entered", async () => {
    const origins = page.getByRole("combobox", { name: "Origin" })
    const destinations = page.getByRole("combobox", { name: "Destination" })
    await fillReferenceAutocomplete(origins.nth(0), "SOF - Sofia Airport")
    await fillReferenceAutocomplete(
      destinations.nth(0),
      "LHR - London Heathrow Airport",
    )
    await page.locator("#builder-2").getByLabel("Departure date").last().fill("2027-02-10")
  })

  await test.step("11 A second itinerary segment is added", async () => {
    await page.getByRole("button", { name: "Add segment" }).click()
    await expect(page.getByRole("combobox", { name: "Origin" })).toHaveCount(2)
  })

  await test.step("12 Second canonical itinerary segment is entered", async () => {
    const origins = page.getByRole("combobox", { name: "Origin" })
    const destinations = page.getByRole("combobox", { name: "Destination" })
    await fillReferenceAutocomplete(
      origins.nth(1),
      "LHR - London Heathrow Airport",
    )
    await fillReferenceAutocomplete(destinations.nth(1), "SOF - Sofia Airport")
    const dates = page.locator("#builder-2").getByLabel("Departure date")
    await dates.last().fill("2027-02-17")
  })

  await test.step("13 Assistance is scoped to one selected segment", async () => {
    await page.getByLabel("All segments").uncheck()
    const assignment = page
      .locator("#builder-4 label")
      .filter({ hasText: "1. Sofia Airport to London Heathrow Airport" })
      .locator('input[type="checkbox"]')
    await assignment.check()
    await expect(assignment).toBeChecked()
  })

  await test.step("14 PETC details are added", async () => {
    await page.getByRole("button", { name: "Add pet" }).click()
    await page.getByLabel("Pet name").fill("Milo")
    await selectFirstRealOption(page.getByLabel("Species"))
    await page.getByLabel("Transport").selectOption("PETC")
    await page.getByLabel("Carrier length cm").fill("48")
    await page.getByLabel("Carrier width cm").fill("32")
    await page.getByLabel("Carrier height cm").fill("30")
  })

  await test.step("15 A special item is added", async () => {
    await page.getByRole("button", { name: "Add special item" }).click()
    await selectFirstRealOption(page.locator("#builder-6 select").first())
    await page.getByLabel("Item name").fill("Folding travel chair")
    await page
      .getByLabel("Description")
      .fill("Compact folding chair requiring manual handling review")
  })

  await test.step("16 Request V4 submits through the UI", async () => {
    const responsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "POST" &&
        /\/api\/agencies\/[^/]+\/requests$/.test(new URL(response.url()).pathname),
    )
    await page.getByRole("button", { name: "Create operational request" }).click()
    const response = await responsePromise
    expect(response.status()).toBe(201)
    await page.waitForURL(
      (url) =>
        /^\/agency\/requests\/[^/]+$/.test(url.pathname) &&
        url.pathname !== "/agency/requests/new",
    )
    requestId = currentPathId(page)
    expect(requestId).toBeTruthy()
    await expect(page.getByText(/Request|Travel request/i).first()).toBeVisible()
  })

  await test.step("17 Request detail preserves canonical lineage", async () => {
    const detail = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/requests/${requestId}`,
    )
    expect(detail.status).toBe(200)
    expect(detail.body.canonical_request?.request_version).toBe(4)
    expect(detail.body.canonical_request?.itinerary_segments).toHaveLength(2)
    expect(detail.body.canonical_request?.pets).toHaveLength(1)
    expect(detail.body.canonical_request?.special_items).toHaveLength(1)
  })

  await test.step("18 Offer preparation workspace opens", async () => {
    await page.goto(`/agency/offers/${OFFER_WORKSPACE_ID}/builder`)
    await expect(
      page.getByRole("heading", { name: "Browser acceptance assisted journey" }),
    ).toBeVisible()
  })

  await test.step("19 Multiple Offer options are visible", async () => {
    await expect(page.getByText("Assisted direct option", { exact: true }).first()).toBeVisible()
    await expect(page.getByText("Flexible assisted option", { exact: true }).first()).toBeVisible()
  })

  await test.step("20 Exact Offer delivery version is available to Portal", async () => {
    await signIn(page, "anna.client@example.com", "/portal")
    await page.goto("/portal/travel-options")
    const deliveryLink = page.locator('a[href^="/portal/travel-options/"]').first()
    await expect(deliveryLink).toBeVisible()
    const href = await deliveryLink.getAttribute("href")
    deliveryId = href.split("/").pop()
    expect(deliveryId).toBeTruthy()
  })

  await test.step("21 Portal Client opens the delivered Offer", async () => {
    await page.goto(`/portal/travel-options/${deliveryId}`)
    await expect(
      page.getByRole("heading", { name: "Your assisted travel options" }),
    ).toBeVisible()
    await expect(page.getByText(/Version 1/).first()).toBeVisible()
  })

  await test.step("22 Internal Offer notes are not exposed to Portal", async () => {
    await expect(page.getByText(INTERNAL_SENTINEL)).toHaveCount(0)
    await expect(page.locator("body")).not.toContainText(INTERNAL_SENTINEL)
  })

  await test.step("23 Portal communication question is recorded safely", async () => {
    const question = "Please confirm wheelchair support at the aircraft door."
    await page
      .getByPlaceholder("Ask about an itinerary, fare, baggage, or assistance requirement")
      .fill(question)
    await page.getByRole("button", { name: "Send Question" }).click()
    await expect(page.getByText(question)).toBeVisible()
    await expect(page.getByText(/No automatic message was sent/i)).toBeVisible()
  })

  await test.step("24 Portal selects the exact itinerary", async () => {
    await page.getByRole("button", { name: "Select this itinerary" }).click()
    await expect(page.getByRole("button", { name: /Economy Flex/ })).toBeVisible()
  })

  await test.step("25 Portal selects the exact fare brand", async () => {
    await page.getByRole("button", { name: /Economy Flex/ }).click()
  })

  await test.step("26 Portal accepts the exact released option", async () => {
    await page.getByRole("button", { name: "Accept Offer" }).click()
    await page
      .getByLabel(/I confirm this selection/)
      .check()
    await page.getByRole("button", { name: "Submit Decision" }).click()
    await expect(
      page.getByRole("heading", { name: "Accepted Offer snapshot" }),
    ).toBeVisible()
  })

  await test.step("27 Immutable accepted snapshot and confirmed Trip exist", async () => {
    await signIn(page, "agency.owner@aeroassist.dev", "/agency")
    const result = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/offer-workspaces/${OFFER_WORKSPACE_ID}/acceptance`,
    )
    expect(result.status).toBe(200)
    expect(result.body.acceptance?.id).toBeTruthy()
    expect(result.body.trip_snapshot?.id).toBeTruthy()
    tripId = result.body.trip_snapshot?.trip_id
    expect(tripId).toBeTruthy()
    const trip = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/trips/${tripId}`,
    )
    expect(trip.status).toBe(200)
    expect(trip.body.trip?.id || trip.body.id).toBe(tripId)
    expect(result.body.booking_readiness?.id).toBeTruthy()
  })

  await test.step("28 Booking preparation opens from canonical acceptance", async () => {
    const result = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/offer-workspaces/${OFFER_WORKSPACE_ID}/acceptance`,
    )
    const acceptance = result.body.acceptance
    const readiness = result.body.booking_readiness
    const query = new URLSearchParams({
      acceptance_id: acceptance.id,
      booking_readiness_package_id: readiness.id,
      trip_id: tripId,
      offer_workspace_id: OFFER_WORKSPACE_ID,
    })
    await page.goto(`/agency/booking-handoffs?${query}`)
    await expect(
      page.getByRole("heading", { name: "Booking Handoffs", level: 1 }),
    ).toBeVisible()
  })

  await test.step("29 Booking readiness handoff is built", async () => {
    await page.getByRole("button", { name: "Build readiness handoff" }).click()
    await expect(page.getByText(/Handoff .*created/i)).toBeVisible()
  })

  await test.step("30 Booking workspace is created without provider execution", async () => {
    await page
      .getByRole("button", { name: "Create booking workspace" })
      .first()
      .click()
    const bookingLink = page.locator('a[href^="/agency/booking-workspaces/"]').first()
    await expect(bookingLink).toBeVisible()
    const href = await bookingLink.getAttribute("href")
    bookingWorkspaceId = href.split("/").pop()
    expect(bookingWorkspaceId).toBeTruthy()
    await bookingLink.click()
  })

  await test.step("31 Booking preparation status is advanced explicitly", async () => {
    await page.getByLabel("Status", { exact: true }).selectOption("booking_in_progress")
    await page.getByLabel("Transition reason").fill("Operator began manual booking.")
    await page.getByRole("button", { name: "Save status" }).click()
    await expect(page.getByText("Booking workspace status updated.")).toBeVisible()
  })

  await test.step("32 Manual Booking result requires evidence", async () => {
    await page.getByLabel("PNR or record locator").fill("BROW57")
    await page.getByLabel("Provider status").selectOption("confirmed")
    await page.getByLabel("Booking result status").selectOption("confirmed")
    await page
      .getByLabel("Source evidence reference")
      .fill("evidence://browser/manual-booking/BROW57")
    await page
      .getByLabel("Operator reason")
      .fill("Manual booking verified against supplier confirmation.")
    await page.getByRole("button", { name: "Record booking result" }).click()
    await expect(
      page.getByText(/Booking result evidence recorded/i),
    ).toBeVisible()
    await expect(page.getByText(/No provider action was executed/i)).toBeVisible()
  })

  await test.step("33 Ticket mirror is created and remains non-executory", async () => {
    await page.getByRole("button", { name: "Add ticket details" }).last().click()
    await page.waitForURL(/\/agency\/tickets\/[^/]+$/)
    ticketId = currentPathId(page)
    await page.getByLabel("Ticket number").fill("125-1234567890")
    await page.getByLabel("Validating carrier").fill("BA")
    await page.getByLabel("Issue status").selectOption("issued")
    await page.getByLabel("Base fare").fill("240")
    await page.getByLabel("Taxes").fill("65")
    await page.getByLabel("Total").fill("305")
    await page.getByRole("button", { name: "Save ticket mirror" }).click()
    await expect(page.getByText("Ticket mirror updated.")).toBeVisible()
    await expect(page.getByRole("button", { name: "Issue ticket" })).toBeDisabled()
  })

  await test.step("34 EMD mirror is created and remains non-executory", async () => {
    await page.goto(`/agency/booking-workspaces/${bookingWorkspaceId}`)
    await page.getByRole("button", { name: "Add EMD details" }).last().click()
    await page.waitForURL(/\/agency\/emds\/[^/]+$/)
    emdId = currentPathId(page)
    await page.getByLabel("EMD number").fill("125-9876543210")
    await page.getByLabel("EMD type").selectOption("emd_a")
    await page.getByLabel("RFIC").fill("A")
    await page.getByLabel("RFISC").fill("0B5")
    await page.getByLabel("Issue status").selectOption("issued")
    await page.getByLabel("Amount").fill("45")
    await page.getByLabel("Total").fill("45")
    await page.getByRole("button", { name: "Save EMD mirror" }).click()
    await expect(page.getByText("EMD mirror updated.")).toBeVisible()
    await expect(page.getByRole("button", { name: "Issue EMD" })).toBeDisabled()
  })

  await test.step("35 Ticket and EMD mirrors are visible from Booking", async () => {
    await page.goto(`/agency/booking-workspaces/${bookingWorkspaceId}`)
    await expect(page.getByText("125-1234567890")).toBeVisible()
    await expect(page.getByText("125-9876543210")).toBeVisible()
  })

  await test.step("36 Invoice is created from the Booking", async () => {
    await page.getByRole("button", { name: "Create linked invoice" }).click()
    await page.waitForURL(/\/agency\/invoices\/[^/]+$/)
    invoiceId = currentPathId(page)
    const invoice = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/invoices/${invoiceId}`,
    )
    expect(invoice.status).toBe(200)
    invoiceNumber = invoice.body.invoice.invoice_number
    expect(invoiceNumber).toBeTruthy()
  })

  await test.step("37 Invoice line and total use governed ledger calculation", async () => {
    await page.getByPlaceholder("Description").fill("Assisted journey services")
    const lineSection = page
      .getByRole("heading", { name: "Line Items" })
      .locator("..")
    await lineSection.locator('input[type="number"]').fill("305")
    await page.getByRole("button", { name: "Add line" }).click()
    await expect(page.getByText(/Assisted journey services/)).toBeVisible()
    await expect(page.getByText("305.00 EUR").first()).toBeVisible()
  })

  await test.step("38 Invoice is issued explicitly", async () => {
    await page.getByRole("button", { name: "Issue", exact: true }).click()
    await expect(page.getByText(/issued/i).first()).toBeVisible()
  })

  await test.step("39 Payment receipt is recorded without gateway execution", async () => {
    const paymentSection = page
      .getByRole("heading", { name: "Payment allocations" })
      .locator("..")
    await paymentSection.locator('input[type="number"]').fill("305")
    await page.getByRole("button", { name: "Record received payment" }).click()
    await expect(page.getByText(/received/i).last()).toBeVisible()
  })

  await test.step("40 Payment is allocated through the governed ledger", async () => {
    const payments = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/payments?invoice_id=${invoiceId}`,
    )
    expect(payments.status).toBe(200)
    expect(payments.body.items).toHaveLength(1)
    expect(payments.body.items[0].status).toBe("received")
    expect(payments.body.items[0].allocated_amount).toBe(305)
    expect(payments.body.items[0].unallocated_amount).toBe(0)
    expect(payments.body.items[0].allocations).toHaveLength(1)
    expect(payments.body.items[0].allocations[0].invoice_id).toBe(invoiceId)
    expect(payments.body.items[0].allocations[0].amount).toBe(305)

    await page.goto("/agency/payments")
    await expect(
      page.getByText(
        /^305\.00 EUR received · 305\.00 EUR allocated · 0\.00 EUR available$/,
      ),
    ).toBeVisible()
    await expect(page.getByRole("link", { name: /305\.00 EUR allocated/i })).toHaveAttribute(
      "href",
      `/agency/invoices/${invoiceId}`,
    )
  })

  await test.step("41 Portal sees safe Invoice and Payment projections", async () => {
    await signIn(page, "anna.client@example.com", "/portal")
    await page.goto(`/portal/invoices/${invoiceId}`)
    await expect(page.getByText(invoiceNumber)).toBeVisible()
    await expect(page.getByText(/305\.00 EUR/).first()).toBeVisible()
    await expect(page.locator("body")).not.toContainText(/supplier cost|margin/i)
  })

  await test.step("42 Portal requested-document upload creates immutable evidence", async () => {
    await page.goto(`/portal/documents/${REQUESTED_DOCUMENT_ID}`)
    await expect(page.getByRole("heading", { name: "Requested passport copy" })).toBeVisible()
    await page.locator('input[type="file"]').setInputFiles({
      name: "passport-copy.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4\n% disposable browser acceptance\n%%EOF\n"),
    })
    await expect(page.getByText("Document uploaded for agency review.")).toBeVisible()
    await expect(page.getByText(/Version 1/)).toBeVisible()
  })

  await test.step("43 Automation exposes internal work without external execution", async () => {
    await signIn(page, "agency.owner@aeroassist.dev", "/agency")
    await page.goto("/agency/work-queue")
    await expect(
      page.getByRole("heading", { name: "Tasks and follow-ups" }),
    ).toBeVisible()
    await page.goto("/agency/task-automation")
    await expect(
      page.getByRole("heading", { name: "Automation rules", exact: true }),
    ).toBeVisible()
    await expect(page.getByText("Human authority remains final")).toBeVisible()
    await expect(page.locator("body")).toContainText(
      "Provider, airline, ticketing, payment, refund, external message, permission, and tenant actions are prohibited.",
    )
  })

  await test.step("44 Shared page search restores keyboard focus", async () => {
    const trigger = page.getByRole("button", { name: "Search Agency pages" })
    await trigger.focus()
    await trigger.click()
    await expect(page.getByRole("textbox", { name: "Search Agency pages" })).toBeFocused()
    await page.keyboard.press("Escape")
    await expect(page.getByRole("dialog", { name: "Search Agency pages" })).toHaveCount(0)
    await expect(trigger).toBeFocused()
  })

  await test.step("45 Approval-required work does not execute automatically", async () => {
    const ticket = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/tickets/${ticketId}`,
    )
    const emd = await browserApi(
      page,
      "GET",
      `/api/agencies/${agencyId}/emds/${emdId}`,
    )
    expect(ticket.status).toBe(200)
    expect(emd.status).toBe(200)
    expect(ticket.body.ticket.provider_execution_enabled).not.toBe(true)
    expect(emd.body.emd.provider_execution_enabled).not.toBe(true)
  })

  await test.step("46 Read-only Agency user cannot mutate", async () => {
    await signIn(page, "agency.readonly@aeroassist.dev", "/agency")
    const result = await browserApi(
      page,
      "POST",
      `/api/agencies/${agencyId}/booking-workspaces/${bookingWorkspaceId}/status`,
      { status: "cancelled", internal_notes: "Must be rejected." },
    )
    expect(result.status).toBe(403)
  })

  await test.step("47 Cross-Agency record access is rejected", async () => {
    await signIn(page, "agency.owner@aeroassist.dev", "/agency")
    const result = await browserApi(
      page,
      "GET",
      `/api/agencies/${OTHER_AGENCY_ID}/requests/${requestId}`,
    )
    expect(result.status).toBe(403)
  })

  await test.step("48 Passenger Portal sees only its mapped Passenger", async () => {
    await signIn(page, "anna.passenger@example.com", "/portal")
    await page.goto("/portal/passengers")
    await expect(page.getByText("Anna Novak").first()).toBeVisible()
    const passengers = await browserApi(page, "GET", "/api/portal/passengers")
    expect(passengers.status).toBe(200)
    expect(passengers.body.items).toHaveLength(1)
    expect(passengers.body.items[0].display_name).toBe("Anna Novak")
  })

  await test.step("49 Unknown routes render Not Found", async () => {
    await page.goto("/definitely-not-an-aeroassist-route")
    await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible()
    await expect(page).toHaveURL(/definitely-not-an-aeroassist-route/)
  })

  await test.step("50 Revoked Portal mapping loses access", async () => {
    await signIn(page, "revoked.client@example.com", "/portal")
    await expect(
      page.getByRole("heading", { name: /Profile link required|Portal access denied/i }),
    ).toBeVisible()
    const portal = await browserApi(page, "GET", "/api/portal/me")
    expect([401, 403]).toContain(portal.status)
  })

  await test.step("51 Browser journey has no uncaught page errors", async () => {
    expect(pageErrors).toEqual([])
  })
})
