# 🌐 IPv6 Subnet Calculator V1.0

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is an offline IPv6 subnet calculator for Windows. It analyzes network ranges, divides subnets, identifies address usage, and provides Calculation, Results, and Address Tools tabs for subnet operations and address/network analysis.

## ✨ Features

- **Network calculations:** IPv6 CIDR `/0`–`/128`, network ranges, subnet counts, addresses per subnet, and additional subnet bits. Includes common prefix shortcuts, address normalization, and Chinese input validation messages.
- **Calculation summary copying:** Use the copy icon at the top right of the network summary to copy ranges, source/target prefixes, exact capacities, and address guidance into planning documents.
- **Address guidance:** Classifies ULA, 6to4, multicast, link-local, and other address types, with usage, deployment limitations, and standards references. Mathematical subnetting remains available for special-purpose addresses.
- **Readability:** Larger interface, input, table, detail, and tooltip text, with adjusted table row heights and dialog space.
- **Appearance:** Light and dark themes, switched with the moon/sun icon at the top right or Ctrl+Shift+T. Your preference is remembered.
- **Three tabs:** Calculation contains inputs, summaries, and usage guidance; Results contains the table and actions; Address Tools contains conversion and network relationship analysis. Each tab retains its state.
- **Address format conversion:** Compressed/lowercase normalized form, eight-group expanded hexadecimal form, and 128-bit binary, with individual and copy-all actions. Accepts IPv4-mapped IPv6 notation.
- **Two-network analysis:** Classifies two IPv6 CIDRs as equal, A containing B, B containing A, adjacent, or independent. Shows exact overlap and gap address counts and copies a complete report.
- **Pagination and location:** 25, 50, 100, or 200 rows per page; page navigation and lookup by IPv6 address, subnet index, or corresponding ranges. Only the current page is loaded, and locator highlighting persists across pages.
- **Selection and copying:** Current-page counts, first and last indices, continuity, and total address capacity. Copy selected subnets, the current page, an index range, or exact statistics. Supports Ctrl/Shift selection, Ctrl+A, Ctrl+C, and Esc.
- **Subnet details:** Double-click or press Enter to inspect full address ranges and capacity, browse adjacent subnets, and copy details.
- **File export:** Export all subnets or a range to TXT or Excel (XLSX), with size estimates, progress, and cancellation. The destination is replaced only after its temporary file is written successfully.

## 🆕 V1.0 Core Feature Release

- **Larger text:** 12 pt interface text, 12 pt monospaced address/results text, and 11 pt binary text, with taller table rows.
- **New address format conversion:** Compressed/normalized, expanded and binary representations with individual and copy-all actions.
- **New two-network relationship analysis:** Equality, directional containment, adjacency and independence, with host-bit normalization.
- **New since V0.9: calculation summary copying.** Copy the full calculation and deployment guidance with exact integers. The action is disabled until a successful calculation and after invalid recalculation.

- Brings together IPv6 subnet calculation, address guidance, pagination and location, selection statistics, copying, details, and TXT/Excel exports into a complete core workflow.
- Provides a consistent PyQt6 three-tab interface, light/dark themes, icon tooltips, and saved theme preferences.
- Provides a standalone Windows package containing the application and project/third-party license files.

### 🐛 Error Handling and Recovery

- Provides clear feedback for invalid networks, prefixes, indices, and ranges.
- Restores controls and allows retries if an export worker cannot start or ends abnormally.
- Preserves existing destination files and removes unfinished temporary files after export failure or cancellation.

## 📸 Screenshots

### Light Theme

![Light Calculation page](docs/screenshots/calculation_light.png)

![Light Results page](docs/screenshots/results_light.png)

![Light Address Tools page](docs/screenshots/tools_light.png)

### Dark Theme

![Dark Calculation page](docs/screenshots/calculation_dark.png)

![Dark Results page](docs/screenshots/results_dark.png)

![Dark Address Tools page](docs/screenshots/tools_dark.png)

## 📦 Download and Usage

Visit this project's Releases page and download `IPv6SubnetCalculator_V1.0.exe` directly from Assets. Run the downloaded executable; Python is not required.

For source execution and building, see [Development Notes](docs/DEVELOPMENT.md).

## 💡 Notes

- Editing an Address Tools input clears only that tool's previous results. Click its icon or press Enter to process again; conversion and analysis retain separate states.
- Conversion accepts one IPv6 address without a prefix or zone ID. Compressed and normalized output share a row using lowercase compressed notation. Binary is displayed in 16-bit groups and copied as 128 consecutive bits.
- Network relationships use normalized CIDRs. Adjacent means non-overlapping, directly contiguous ranges; it does not guarantee they form one CIDR. The gap count counts addresses between the two ranges.
- The first launch uses the light theme; subsequent launches restore your choice. Hover over the theme icon to see the current theme, next theme, and shortcut. Native file pickers and title bars follow the operating system.

- Summary copying uses the last successful calculation shown on the page. Recalculate after editing inputs to update it.
- The default example network is `2026:1015:abcd::/48`.
- IPv6 has no broadcast address; the end address is the last address in the network. Address capacity is a mathematical total, not an assignable host count.
- Manual selection applies only to the current page and clears on page or page-size changes. Switching tabs preserves selection. Locator highlighting is counted separately.
- Changing page size uses the original page's first subnet as the navigation anchor.
- Index-range copying supports up to 5,000 records per operation; use file export for larger ranges.
- One Excel worksheet supports up to 1,048,575 subnet records. If the export includes indices longer than 15 digits, the entire index column is stored as text to preserve every digit.
- Very large statistics use compact display formatting. Hover for full values; copied statistics always contain exact integers.
- Address classification does not imply allocation authorization or public reachability. See the [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry).

## 📄 License

Project-authored code and assets are licensed under the **GNU General Public License v3.0 or any later version** (`GPL-3.0-or-later`). See [NOTICE](NOTICE) for the scope and notice, and [LICENSE](LICENSE) for the full terms. Use, modification, and commercial redistribution are permitted subject to the license. This software comes without any warranty.

Third-party components retain their own copyrights and licenses; this project's license declaration does not change them.

## 🙏 Third-Party Components

The interface uses PyQt6 and Qt 6. Copyright, license information, and upstream links are listed in [Third-Party Notices](THIRD_PARTY_NOTICES.md).
