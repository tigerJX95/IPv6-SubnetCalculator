# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
#
# This file is part of IPv6SubnetCalculator.
# IPv6SubnetCalculator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IPv6SubnetCalculator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IPv6SubnetCalculator. If not, see <https://www.gnu.org/licenses/>.

"""发布自检必须完成的工作流，供源码和打包验证共同使用。"""
REQUIRED_RELEASE_CHECKS = frozenset(('translation_catalog_integrity_and_templates', 'membership_cidr_output_preserves_containment', 'coverage_cidr_categories_exact_and_importable', 'list_address_membership_preserves_all_matches', 'list_coverage_comparison_exact_delta_and_invalidation', 'planning_unsaved_cancel_preserves_draft', 'planning_project_inputs_restore_without_stale_results', 'about_help_licenses_legal_offline', 'calculation_summary_snapshot', 'address_formats_and_network_relations', 'plan_save_and_restore_with_unicode_path', 'shared_plan_import_chinese_catalog_and_input_error_recovery', 'default_calculation_and_resources', 'maximum_ipv6_space_and_last_page', 'address_range_exact_coverage_and_bilingual_state', 'bilingual_live_switch_preserves_calculation_view_and_license_originals', 'file_metadata_and_component_overview_follow_language', 'subnet_list_unicode_import_and_background_relations', 'list_txt_output_and_localized_report', 'parent_free_space_exact_union_and_difference', 'aligned_allocation_exact_capacity_bilingual_snapshot', 'cidr_aggregation_preserves_coverage_and_input', 'planning_txt_output_and_transfer_actions', 'subnet_list_cancel_preserves_input', '100_navigation_selection_cycles', 'background_txt_export_with_unicode_path', 'english_xlsx_headers_and_frozen_export_language', 'background_xlsx_export_with_unicode_path', 'cancel_preserves_original_and_cleans_temporary_file', 'save_conflict_preserves_other_writer_and_complete_output'))
