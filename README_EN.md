# 🌐 IPv6 Subnet Calculator V0.5

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is an offline IPv6 subnet calculator for Windows. It calculates network ranges, divides subnets, identifies special-purpose address space, and provides two tabs for calculating and browsing large result sets.

## ✨ Features

- **Subnet calculations:** IPv6 CIDR `/0`–`/128`, network range, subnet counts, and addresses per subnet; lowercase normalization and clear input validation.
- **Prefix and usage analysis:** Common prefix shortcuts, additional subnet bits, special-purpose classifications including ULA, 6to4, multicast and link-local, and deployment guidance with standards references.
- **Two-tab layout:** Use the Calculation tab for inputs, summaries, and address guidance, and the Results tab for the complete table and actions. Switching tabs preserves pagination and locator ranges.
- **Pagination and location:** 25, 50, 100, or 200 rows per page, page navigation, and lookup by IPv6 address, subnet number, address range, or subnet-number range. Range highlighting continues across pages.
- **Selection statistics:** Counts selected rows and highlighted range matches **on the current page** and refreshes the counts as selection and pages change.
- **Copy and inspect:** Copy selected rows, the current page, or a specified subnet-number range (up to 5,000 rows per copy). Double-click a row for subnet details and adjacent-record navigation.
- **Export:** Export all or a selected range to TXT or Excel (XLSX), with size estimates, progress tracking, and cancellation.

## 🆕 What's New in V0.5

- Introduced Calculation and Results tabs, with full browsing, pagination, locating, copying, and exporting on the Results tab.
- Kept the Calculation tab focused on summaries and address guidance, without a cramped preview table.
- Added current-page selected-row and range-highlight counts.
- Preserved page and locator state when switching tabs.

## 📦 Download and Usage

Get the Windows application from GitHub [Releases](../../releases). Enter a network and target prefix, calculate, then switch to the Results tab to browse the full list.

## 💡 Notes

- The default example network is `2026:1015:abcd::/48`.
- IPv6 has no broadcast address; the displayed end address is the last address in the range.
- Selection and highlight counts refer only to the **currently displayed page**, not an entire multi-page range.
- Excel exports support at most 1,048,575 subnet records in one worksheet; use TXT for larger exports.
- Address classification does not imply allocation authorization or public reachability. See the [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry).
