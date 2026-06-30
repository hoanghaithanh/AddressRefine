# Traceability Matrix — AddressRefine

Status: Living document, added to on every BA pass. Links each acceptance
criterion to its source requirement, the test the `tester` agent is
expected to produce, and current status.

## M1 — Scaffold + Upload + Mapping (backfilled)

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-1.1, FR-1.5 | AC-M1-1 | `tests/test_routers/test_upload.py::test_get_upload_form_returns_200_with_form` | Done |
| FR-1.1, FR-1.5 | AC-M1-2 | `tests/test_routers/test_upload.py::test_post_upload_valid_csv_redirects_to_mapping_and_sets_cookie` | Done |
| FR-1.2 | AC-M1-3 | `tests/test_routers/test_upload.py::test_post_upload_oversized_file_does_not_redirect` | Done |
| FR-1.3 | AC-M1-4 | `tests/test_routers/test_upload.py::test_post_upload_garbage_empty_csv_returns_400` | Done |
| FR-1.3 | AC-M1-5 | `tests/test_compute/test_pandas_backend.py::test_load_csv_header_only_raises_value_error` | Done |
| FR-1.4 | AC-M1-6 | `tests/test_compute/test_pandas_backend.py::test_extract_columns_preserves_leading_zero_zip` | Done |
| FR-1.4 | AC-M1-7 | `tests/test_compute/test_pandas_backend.py::test_extract_columns_preserves_literal_na_string` | Done |
| FR-2.1 (extract shape) | AC-M1-8 | `tests/test_compute/test_pandas_backend.py::test_extract_columns_unmapped_logical_column_is_empty_string` | Done |
| FR-2.2 | AC-M1-9 | `tests/test_routers/test_mapping.py::test_get_mapping_after_upload_shows_headers_with_best_guess_selected` | Done |
| FR-2.7 | AC-M1-10 | `tests/test_routers/test_mapping.py::test_get_mapping_without_upload_redirects_to_root` | Done |
| FR-2.4, FR-2.6 (superseded by FR-2.6 update, see AC-M2-24) | AC-M1-11 | `tests/test_routers/test_mapping.py::test_post_mapping_valid_redirects_to_algorithm` | Done (updated for M2's redirect-target change) |
| FR-2.5 | AC-M1-12 | `tests/test_routers/test_mapping.py::test_post_mapping_street_col_not_a_real_header_returns_422` | Done |
| FR-2.5 | AC-M1-13 | `tests/test_routers/test_mapping.py::test_post_mapping_zip_col_not_a_real_header_returns_422` | Done |
| FR-2.4 | AC-M1-14 | `tests/test_routers/test_mapping.py::test_post_mapping_without_zip_or_city_returns_422` | Done |
| FR-2.3 | AC-M1-15 | `tests/test_routers/test_mapping.py::test_post_mapping_then_get_shows_chosen_mapping_not_best_guess` | Done |
| FR-6.1 (stub) | (M1 stub behavior) | `tests/test_compute/test_pandas_backend.py::test_replace_values_raises_not_implemented` | Done |

## M2 — Fingerprint + N-Gram Fingerprint Algorithms + Read-Only Results (done)

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-3.1 | AC-M2-1 | `tests/test_algorithms/test_base.py::test_matching_algorithm_abc_shape` | Done |
| FR-4.3 | AC-M2-2 | `tests/test_algorithms/test_base.py::test_algorithm_output_carries_clusters_for_key_collision` | Done |
| FR-3.1, FR-3.3 | AC-M2-3 | `tests/test_algorithms/test_registry.py::test_list_algorithms_includes_fingerprint_and_ngram` | Done |
| FR-4.2 | AC-M2-4 | `tests/test_algorithms/test_fingerprint.py::test_normalization_case_and_punctuation_insensitive` | Done |
| FR-4.2 | AC-M2-5 | `tests/test_algorithms/test_fingerprint.py::test_normalization_collapses_whitespace` | Done |
| FR-4.2 | AC-M2-6 | `tests/test_algorithms/test_fingerprint.py::test_token_order_does_not_affect_key` | Done |
| FR-4.2 | AC-M2-7 | `tests/test_algorithms/test_fingerprint.py::test_duplicate_tokens_deduplicated` | Done |
| FR-4.2 | AC-M2-8 | `tests/test_algorithms/test_fingerprint.py::test_non_matching_addresses_not_clustered` | Done |
| FR-4.2 | AC-M2-9 | `tests/test_algorithms/test_fingerprint.py::test_blank_address_excluded_from_clustering` | Done |
| FR-4.2 | AC-M2-10 | `tests/test_services/test_matching_service.py::test_singleton_keys_produce_no_candidate_pair` | Done |
| FR-3.3 | AC-M2-11 | `tests/test_algorithms/test_ngram_fingerprint.py::test_default_n_is_2` | Done |
| FR-4.2 | AC-M2-12 | `tests/test_algorithms/test_ngram_fingerprint.py::test_ngram_key_construction_uses_hyphen_delimiter` | Done |
| FR-4.2 | AC-M2-13 | `tests/test_algorithms/test_ngram_fingerprint.py::test_strings_shorter_than_n_excluded` | Done |
| FR-3.4 | AC-M2-14 | `tests/test_algorithms/test_ngram_fingerprint.py::test_different_n_can_change_cluster_assignments` | Done |
| FR-4.1 | AC-M2-15 | `tests/test_services/test_matching_service.py::test_run_matching_uses_extract_street_addresses` | Done |
| FR-4.1 | AC-M2-16 | `tests/test_services/test_matching_service.py::test_run_matching_rebuilds_candidate_pairs_from_scratch` | Done |
| FR-4.2 | AC-M2-17 | `tests/test_services/test_matching_service.py::test_cluster_becomes_one_candidate_pair_entry_not_pairwise` | Done |
| FR-3.2 | AC-M2-18 | `tests/test_routers/test_algorithm.py::test_get_algorithm_lists_fingerprint_and_ngram` | Done |
| FR-3.2 | AC-M2-19 | `tests/test_routers/test_algorithm.py::test_get_algorithm_without_mapping_redirects_to_mapping` | Done |
| FR-3.4 | AC-M2-20 | `tests/test_routers/test_algorithm.py::test_post_algorithm_persists_choice_and_runs_matching` | Done |
| FR-5.1 | AC-M2-21 | `tests/test_routers/test_results.py::test_get_results_renders_groups_readonly` | Done |
| FR-5.1 | AC-M2-21a | `tests/test_routers/test_results.py::test_get_results_distance_column_blank_for_key_collision` | Done |
| FR-5.1 | AC-M2-22 | `tests/test_routers/test_results.py::test_get_results_without_algorithm_redirects_to_algorithm` | Done |
| FR-4.3 | AC-M2-23 | `tests/test_algorithms/test_backend_agnosticism.py::test_algorithms_file_does_not_import_pandas` (parametrized over each file in `app/algorithms/`) and `::test_matching_service_does_not_import_pandas` | Done |
| FR-2.6 (updated) | AC-M2-24 | `tests/test_routers/test_mapping.py::test_post_mapping_valid_redirects_to_algorithm` | Done |
| FR-3.4 | AC-M2-25 | `tests/test_routers/test_algorithm.py::test_post_algorithm_invalid_n_zero_returns_422`, `::test_post_algorithm_invalid_n_negative_returns_422`, `::test_post_algorithm_invalid_n_non_integer_returns_422`, `::test_post_algorithm_invalid_n_does_not_persist_or_run_matching` | Done |
| FR-5.1 | AC-M2-26 | `tests/test_routers/test_results.py::test_get_results_empty_state_suggests_next_action` | Done |

## M3 — Levenshtein + NCD/PPM Algorithms + Blocking (done)

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-4.5 | AC-M3-1 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_groups_rows_by_3char_zip_prefix`, `::test_compute_blocks_block_key_equals_3char_prefix` | Done |
| FR-4.5 | AC-M3-2 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_short_zip_2chars_uses_full_string`, `::test_compute_blocks_short_zip_1char_uses_full_string` | Done |
| FR-4.5 | AC-M3-3 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_city_fallback_when_zip_blank`, `::test_compute_blocks_city_block_is_separate_from_zip_block`, `::test_compute_blocks_city_key_is_normalized_lowercase` | Done |
| FR-4.5 | AC-M3-4 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_unblocked_when_no_zip_or_city`, `::test_compute_blocks_unblocked_rows_not_in_zip_or_city_blocks` | Done |
| FR-4.5 | AC-M3-5 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_zip_normalization_strips_whitespace`, `::test_compute_blocks_zip_normalization_lowercases`, `::test_compute_blocks_city_normalization_strips_whitespace`, `::test_compute_blocks_city_normalization_lowercases` | Done |
| FR-4.3, FR-4.5 | AC-M3-6 | `tests/test_algorithms/test_blocking.py::test_blocking_module_does_not_import_pandas`, `::test_compute_blocks_accepts_only_dict_argument`, `::test_compute_blocks_returns_dict_of_str_to_list_of_int` | Done |
| FR-4.6 | AC-M3-7 | `tests/test_algorithms/test_ncd.py::test_ncd_identical_strings_returns_zero`, `::test_ncd_identical_long_strings_returns_zero` | Done |
| FR-4.6 | AC-M3-8 | `tests/test_algorithms/test_ncd.py::test_ncd_dissimilar_pair_greater_than_similar_pair`, `::test_ncd_address_variants_are_more_similar_than_random` (revised to a relative assertion — see note below) | Done |
| FR-4.6 | AC-M3-9 | `tests/test_algorithms/test_ncd.py::test_ncd_is_symmetric_basic`, `::test_ncd_is_symmetric_address_strings`, `::test_ncd_is_symmetric_mixed_lengths` | Done |
| FR-4.6 | AC-M3-10 | `tests/test_algorithms/test_ncd.py::test_ncd_both_empty_strings_returns_zero` | Done |
| FR-3.5 | AC-M3-11 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_registered_with_correct_key_label_family`, `::test_get_algorithm_levenshtein_returns_correct_instance` | Done |
| FR-3.5 | AC-M3-12 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_param_specs_threshold` | Done |
| FR-4.7 | AC-M3-13 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_pairs_within_threshold`, `::test_levenshtein_pairs_contain_distance_field` | Done |
| FR-4.7 | AC-M3-14 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_does_not_pair_above_threshold` | Done |
| FR-4.7 | AC-M3-15 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_threshold_zero_matches_only_identical`, `::test_levenshtein_threshold_zero_does_not_pair_different_strings` | Done |
| FR-4.5, FR-4.7 | AC-M3-16 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_respects_block_boundaries` | Done |
| FR-4.7 | AC-M3-17 | `tests/test_algorithms/test_nearest_neighbor.py::test_levenshtein_uses_rapidfuzz_with_score_cutoff` | Done |
| FR-3.5 | AC-M3-18 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_registered_with_correct_key_label_family`, `::test_get_algorithm_ncd_returns_correct_instance` | Done |
| FR-3.5 | AC-M3-19 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_param_specs_threshold` | Done |
| FR-4.6 | AC-M3-20 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_threshold_scaling_documented_in_source`, `::test_ncd_threshold_scaling_behavioral` | Done |
| FR-4.6 | AC-M3-21 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_pairs_within_threshold`, `::test_ncd_pairs_contain_distance_field` | Done |
| FR-4.6 | AC-M3-22 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_does_not_pair_above_threshold` | Done |
| FR-4.5, FR-4.6 | AC-M3-23 | `tests/test_algorithms/test_nearest_neighbor.py::test_ncd_respects_block_boundaries` | Done |
| FR-4.4, FR-4.5 | AC-M3-24 | `tests/test_services/test_matching_service_m3.py::test_run_matching_nn_calls_extract_columns` | Done |
| FR-4.4 | AC-M3-25 | `tests/test_services/test_matching_service_m3.py::test_run_matching_key_collision_passes_none_blocks` | Done |
| FR-4.4 | AC-M3-26 | `tests/test_services/test_matching_service_m3.py::test_run_matching_union_find_merges_transitive_pairs` | Done |
| FR-4.4 | AC-M3-27 | `tests/test_services/test_matching_service_m3.py::test_run_matching_distance_is_max_pairwise_in_cluster` | Done |
| FR-4.4 | AC-M3-28 | `tests/test_services/test_matching_service_m3.py::test_run_matching_nn_assigns_unique_pair_ids`, `::test_run_matching_key_collision_assigns_unique_pair_ids` | Done |
| FR-4.1 | AC-M3-29 | `tests/test_services/test_matching_service_m3.py::test_run_matching_nn_rebuilds_candidate_pairs_from_scratch`, `::test_run_matching_nn_produces_fresh_pair_ids_on_repeated_calls` | Done |
| FR-4.4 | AC-M3-30 | `tests/test_services/test_matching_service_m3.py::test_candidate_pair_has_pair_id_field`, `::test_candidate_pair_distance_field_still_present` | Done |
| FR-3.5, FR-3.4 | AC-M3-31 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_levenshtein_threshold_zero_accepted`, `::test_post_algorithm_levenshtein_threshold_1_accepted`, `::test_post_algorithm_levenshtein_default_threshold_accepted`, `::test_post_algorithm_levenshtein_threshold_10_accepted`, `::test_post_algorithm_levenshtein_persists_algorithm_key_and_params` | Done |
| FR-3.5, FR-3.4 | AC-M3-32 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_levenshtein_negative_threshold_returns_422`, `::test_post_algorithm_levenshtein_non_integer_threshold_returns_422`, `::test_post_algorithm_levenshtein_alphabetic_threshold_returns_422`, `::test_post_algorithm_levenshtein_invalid_does_not_persist` | Done |
| FR-3.5, FR-3.4 | AC-M3-33 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_ncd_threshold_1_accepted`, `::test_post_algorithm_ncd_threshold_3_accepted`, `::test_post_algorithm_ncd_threshold_10_accepted`, `::test_post_algorithm_ncd_persists_algorithm_key_and_params` | Done |
| FR-3.5, FR-3.4 | AC-M3-34 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_ncd_threshold_zero_returns_422`, `::test_post_algorithm_ncd_threshold_zero_does_not_run_matching` | Done |
| FR-3.5, FR-3.4 | AC-M3-35 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_ncd_threshold_11_returns_422`, `::test_post_algorithm_ncd_threshold_100_returns_422`, `::test_post_algorithm_ncd_threshold_non_integer_returns_422` | Done |
| FR-3.5, FR-3.4 | AC-M3-36 | `tests/test_routers/test_algorithm_m3.py::test_post_algorithm_fingerprint_ignores_threshold`, `::test_post_algorithm_fingerprint_ignores_negative_threshold`, `::test_post_algorithm_ngram_ignores_threshold_validation` | Done |
| FR-3.5 | AC-M3-37 | `tests/test_routers/test_algorithm_m3.py::test_get_algorithm_page_contains_threshold_input_field`, `::test_get_algorithm_page_threshold_shown_when_levenshtein_selected`, `::test_get_algorithm_page_threshold_hidden_for_key_collision` | Done |
| FR-5.1 | AC-M3-38 | `tests/test_routers/test_results_m3.py::test_results_levenshtein_shows_edit_distance_sublabel`, `::test_results_levenshtein_distance_sublabel_near_distance_header` | Done |
| FR-5.1 | AC-M3-39 | `tests/test_routers/test_results_m3.py::test_results_ncd_shows_ncd_score_sublabel`, `::test_results_ncd_distance_sublabel_class_present` | Done |
| FR-5.1 | AC-M3-40 | `tests/test_routers/test_results_m3.py::test_results_fingerprint_has_no_nn_sublabel`, `::test_results_ngram_fingerprint_has_no_nn_sublabel`, `::test_results_fingerprint_distance_column_still_shows_em_dash` | Done |
| FR-4.3 | AC-M3-41 | `tests/test_algorithms/test_blocking.py::test_blocking_module_does_not_import_pandas`, `tests/test_algorithms/test_ncd.py::test_ncd_module_does_not_import_pandas`, `tests/test_algorithms/test_nearest_neighbor.py::test_nearest_neighbor_module_does_not_import_pandas` | Done |

## chore-frontend-redesign — OpenRefine-Style Frontend Redesign

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-9.1 | AC-CHORE-1 | `tests/test_static/test_design_tokens.py::test_root_defines_required_color_custom_properties` | Planned |
| FR-9.2 | AC-CHORE-2 | `tests/test_static/test_design_tokens.py::test_root_defines_required_spacing_custom_properties` | Planned |
| FR-9.3 | AC-CHORE-3 | `tests/test_static/test_no_inline_styles.py::test_no_template_contains_inline_style_attribute` | Planned |
| FR-9.4 | AC-CHORE-4 | `tests/test_static/test_design_tokens.py::test_site_header_rule_uses_header_color_tokens` | Planned |
| FR-9.5 | AC-CHORE-5 | `tests/test_templates/test_mapping_layout.py::test_mapping_fields_wrapped_in_control_row_and_group`, `::test_mapping_field_attributes_unchanged` | Planned |
| FR-9.5 | AC-CHORE-6 | `tests/test_templates/test_algorithm_layout.py::test_algorithm_fields_wrapped_in_control_row_and_group`, `::test_algorithm_field_attributes_unchanged` | Planned |
| FR-9.6 | AC-CHORE-7 | `tests/test_templates/test_button_classes.py::test_upload_button_has_btn_primary_class`, `::test_mapping_button_has_btn_primary_class`, `::test_algorithm_button_has_btn_primary_class` | Planned |
| FR-9.7 | AC-CHORE-8 | `tests/test_static/test_design_tokens.py::test_results_table_header_row_shading_rule_exists`, `::test_results_table_zebra_striping_rules_exist`, `::test_results_table_hover_rule_exists` | Planned |
| FR-9.8 | AC-CHORE-9 | `tests/test_static/test_design_tokens.py::test_disabled_button_rule_exists_and_distinct`, `tests/test_templates/test_button_classes.py::test_pair_row_accept_reject_buttons_have_btn_class` | Planned |
| FR-9.1–FR-9.8 | AC-CHORE-10 | full existing `pytest -q` suite (M1–M3 tests unmodified, zero new failures) | Planned |
| FR-9.9 | AC-CHORE-11, AC-CHORE-12, AC-CHORE-13, AC-CHORE-14 | tester's Visual QA pass (Playwright screenshots vs. `docs/design/reference/screenshots/`); reported as Visual — Must fix / Visual — Informational, not a `pytest` case | Planned |

## M4 — Combined Algorithm/Results Page + Pairwise Merge

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-3.2 | AC-M4-1 | `tests/test_routers/test_algorithm_m4.py::test_get_algorithm_renders_method_field_with_nn_and_fingerprint_options` | Done |
| FR-3.2 | AC-M4-2 | `tests/test_routers/test_algorithm_m4.py::test_get_algorithm_distance_function_options_present_for_all_four_algorithms`, `::test_get_algorithm_distance_function_labels_match_registry` (option filtering itself is client-side per `match.js`; the router test asserts every option + its `data-family` attribute is present in the rendered HTML for the JS to filter) | Done |
| FR-3.3 | AC-M4-3 | `tests/test_routers/test_algorithm_m4.py::test_get_algorithm_radius_label_shown_for_levenshtein`, `::test_get_algorithm_radius_label_shown_for_ncd` | Done |
| FR-3.3 | AC-M4-4 | `tests/test_routers/test_algorithm_m4.py::test_get_algorithm_no_param_field_for_fingerprint` | Done |
| FR-3.3 | AC-M4-5 | `tests/test_routers/test_algorithm_m4.py::test_get_algorithm_ngram_size_label_shown_for_ngram_fingerprint` | Done |
| FR-3.4 | AC-M4-6 | `tests/test_routers/test_algorithm_m4.py::test_recompute_change_method_to_nn_reruns_with_default_nn_algorithm` | Done |
| FR-3.4 | AC-M4-7 | `tests/test_routers/test_algorithm_m4.py::test_recompute_change_distance_function_reruns_matching` | Done |
| FR-3.4 | AC-M4-8 | `tests/test_routers/test_algorithm_m4.py::test_recompute_change_radius_reruns_matching_with_new_threshold`, `::test_recompute_change_ngram_size_reruns_matching` | Done |
| FR-3.4 | AC-M4-9 | `tests/test_routers/test_algorithm_m4.py::test_recompute_invalid_levenshtein_threshold_negative_returns_422`, `::test_recompute_invalid_ncd_threshold_zero_returns_422`, `::test_recompute_invalid_ncd_threshold_above_ten_returns_422`, `::test_recompute_invalid_ngram_size_zero_returns_422`, `::test_recompute_invalid_ngram_size_non_integer_returns_422`, `::test_recompute_invalid_param_does_not_mutate_session_or_run_matching`, `::test_recompute_unknown_algorithm_key_returns_422` | Done |
| FR-3.7 | AC-M4-10 | `tests/test_routers/test_algorithm_m4.py::test_get_results_redirects_to_algorithm`, `::test_get_results_redirects_regardless_of_session_state` | Done |
| FR-4.2 | AC-M4-11 | `tests/test_services/test_matching_service_m4.py::test_key_collision_cluster_of_three_explodes_into_three_pairs`, `::test_ngram_fingerprint_cluster_of_three_explodes_into_three_pairs` | Done |
| FR-4.2 | AC-M4-12 | `tests/test_services/test_matching_service_m4.py::test_key_collision_pair_distance_is_none` | Done |
| FR-4.4 | AC-M4-13 | `tests/test_services/test_matching_service_m4.py::test_nn_transitive_abc_produces_two_separate_pairs_not_one_cluster` | Done |
| FR-4.4 | AC-M4-14 | `tests/test_services/test_matching_service_m4.py::test_nn_pair_distance_is_the_single_pairwise_distance_not_a_max` | Done |
| FR-4.4 | AC-M4-15 | `tests/test_services/test_matching_service_m4.py::test_candidate_pair_row_indices_always_length_two` (parametrized over fingerprint, ngram_fingerprint, levenshtein, ncd) | Done |
| FR-4.1 | AC-M4-16 | `tests/test_services/test_matching_service_m4.py::test_run_matching_rebuilds_candidate_pairs_from_scratch_with_fresh_pair_ids` | Done |
| FR-5.2 | AC-M4-17 | `tests/test_routers/test_algorithm_m4.py::test_results_table_renders_merge_checkbox_unchecked_by_default` | Done |
| FR-5.2 | AC-M4-18 | `tests/test_routers/test_algorithm_m4.py::test_results_table_distance_column_shown_for_nn_pairs`, `::test_results_table_distance_column_omitted_for_fingerprint_pairs` | Done |
| FR-5.2 | AC-M4-19 | `tests/test_routers/test_algorithm_m4.py::test_results_table_renders_two_addresses_per_row_as_clickable_elements` | Done |
| FR-5.3 | AC-M4-20 | `tests/test_routers/test_algorithm_m4.py::test_new_cell_value_input_is_not_readonly_or_disabled` | Done |
| FR-5.4 | AC-M4-21 | `tests/test_frontend/test_match_js.py::test_checking_merge_without_clicking_address_defaults_new_cell_value_to_first_address` (Playwright, driven against the live combined page through the real upload -> mapping -> recompute flow; module is skipped if Chromium isn't installed) | Done |
| FR-5.5 | AC-M4-22 | `tests/test_frontend/test_match_js.py::test_clicking_either_address_sets_new_cell_value_and_checks_merge_checkbox`, `::test_clicking_address_overrides_prior_checkbox_state_regardless` | Done |
| FR-5.6 | AC-M4-23 | `tests/test_frontend/test_match_js.py::test_new_cell_value_remains_editable_after_being_defaulted`, `::test_new_cell_value_remains_editable_after_address_click` | Done |
| FR-5.6 (no accept/reject routes) | AC-M4-24 | `tests/test_routers/test_algorithm_m4.py::test_no_accept_reject_or_representative_endpoints_registered`, `::test_only_merge_is_a_mutating_post_route_on_results_flow` (statically asserts the FastAPI route table has no `POST /results/pair/*` route) | Done |
| FR-6.2 | AC-M4-25 | `tests/test_services/test_merge_service.py::test_apply_merge_rewrites_both_rows_in_checked_pair_to_new_value` | Done |
| FR-6.2 | AC-M4-26 | `tests/test_services/test_merge_service.py::test_apply_merge_is_idempotent_when_one_side_already_equals_new_value` | Done |
| FR-6.3 | AC-M4-27 | `tests/test_services/test_merge_service.py::test_apply_merge_blocks_on_conflicting_targets_for_same_row`, `::test_apply_merge_blocked_merge_does_not_call_replace_values` | Done |
| FR-6.3 | AC-M4-28 | `tests/test_services/test_merge_service.py::test_apply_merge_blocked_merge_mutates_nothing`, `::test_apply_merge_conflict_error_lists_conflicting_row_and_values` | Done |
| FR-6.4 | AC-M4-29 | `tests/test_services/test_merge_service.py::test_apply_merge_appends_new_dataset_version_with_created_from_merge_true` | Done |
| FR-6.4 | AC-M4-30 | `tests/test_services/test_merge_service.py::test_apply_merge_reruns_matching_with_currently_selected_algorithm_and_params`, `::test_apply_merge_actually_reruns_matching_end_to_end` | Done |
| FR-6.5 | AC-M4-31 | `tests/test_services/test_merge_service.py::test_apply_merge_zero_checked_rows_is_noop_no_version_appended`, `::test_apply_merge_zero_checked_rows_does_not_invoke_run_matching` | Done |
| FR-6.1 | AC-M4-32 | `tests/test_routers/test_merge_m4.py::test_post_merge_only_includes_checked_rows_in_request`, `::test_post_merge_empty_request_is_a_noop_and_returns_200` | Done |
| FR-6.2, FR-6.4 | AC-M4-33 | `tests/test_routers/test_merge_m4.py::test_post_merge_success_returns_refreshed_results_table_partial`, `::test_post_merge_success_appends_dataset_version` | Done |
| FR-6.3 | AC-M4-34 | `tests/test_routers/test_merge_m4.py::test_post_merge_conflict_returns_422_and_does_not_mutate_session` | Done |
| compute/backend.py | AC-M4-35 | `tests/test_compute/test_pandas_backend.py::test_replace_values_sets_street_col_at_given_indices`, `::test_replace_values_multiple_row_indices` | Done |
| compute/backend.py | AC-M4-36 | `tests/test_compute/test_pandas_backend.py::test_replace_values_does_not_raise_not_implemented` (supersedes M1's `test_replace_values_raises_not_implemented`, removed) | Done |
| FR-9 (extends) | AC-M4-37 | `tests/test_routers/test_algorithm_m4.py::test_algorithm_html_has_no_inline_style_attribute`, `::test_results_table_partial_has_no_inline_style_attribute` | Done |

Superseded/removed in this pass (M2/M3-era assertions that M4 deliberately
supersedes, not regressions — see `m4-merge-review.md`'s "M3 reversal"
callout):

- `tests/test_routers/test_algorithm.py`, `test_algorithm_m3.py` — asserted
  a `POST /algorithm` form-submit-then-redirect-to-`/results` flow that no
  longer exists (replaced by `POST /algorithm/recompute` returning a
  partial). Deleted; superseded by `test_algorithm_m4.py`.
- `tests/test_routers/test_results.py`, `test_results_m3.py` — asserted a
  standalone `/results` page (disabled Accept/Reject buttons, distance
  sub-labels) that M4 removes entirely. Deleted; `GET /results` is now
  covered as a redirect-only route in `test_algorithm_m4.py`.
- `tests/test_services/test_matching_service_m3.py` — asserted transitive
  union-find clustering and "distance = max pairwise distance in cluster",
  both reversed by M4 (AC-M4-13/14). Deleted; superseded by
  `test_matching_service_m4.py`.
- `tests/test_frontend/test_design_chore.py` — asserted pre-M4
  `algorithm.html`/`results.html` structure (separate `n`/`threshold`
  control-groups, disabled Accept/Reject buttons on `_pair_row.html`) that
  no longer matches the merged M4 template. Deleted; the still-relevant
  CSS-token/no-inline-style assertions are not M4-specific and weren't
  reintroduced as a separate file since no new design-system rules were
  added in M4 (FR-9 regression is covered by AC-M4-37 above instead).
- `tests/test_services/test_matching_service.py::test_cluster_becomes_one_candidate_pair_entry_not_pairwise` —
  renamed to `test_cluster_of_three_explodes_into_three_pairwise_entries` and
  rewritten to assert the new pairwise-explosion behavior (was asserting
  the now-superseded M2 single-multi-row-entry behavior).
- `tests/test_compute/test_pandas_backend.py::test_replace_values_raises_not_implemented` —
  replaced with `test_replace_values_sets_street_col_at_given_indices` /
  `test_replace_values_multiple_row_indices` / `test_replace_values_does_not_raise_not_implemented`
  now that M4 implements `replace_values` for real (AC-M4-35/36).

## M5

Not yet authored — to be added by the BA pass that runs before M5's
`coder` pass starts.
