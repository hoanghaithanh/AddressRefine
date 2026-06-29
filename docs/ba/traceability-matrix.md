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

## M3 — Levenshtein + NCD/PPM Algorithms + Blocking (in progress)

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-4.5 | AC-M3-1 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_groups_by_zip_prefix` | Planned |
| FR-4.5 | AC-M3-2 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_uses_full_zip_when_shorter_than_3_chars` | Planned |
| FR-4.5 | AC-M3-3 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_falls_back_to_city_when_zip_blank` | Planned |
| FR-4.5 | AC-M3-4 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_unblocked_bucket_when_no_zip_or_city` | Planned |
| FR-4.5 | AC-M3-5 | `tests/test_algorithms/test_blocking.py::test_compute_blocks_normalizes_whitespace_and_case` | Planned |
| FR-4.3, FR-4.5 | AC-M3-6 | `tests/test_algorithms/test_backend_agnosticism.py::test_algorithms_file_does_not_import_pandas` (extended to cover `blocking.py`) | Planned |
| FR-4.6 | AC-M3-7 | `tests/test_algorithms/test_ncd.py::test_ncd_identical_strings_is_zero` | Planned |
| FR-4.6 | AC-M3-8 | `tests/test_algorithms/test_ncd.py::test_ncd_dissimilar_strings_is_high` | Planned |
| FR-4.6 | AC-M3-9 | `tests/test_algorithms/test_ncd.py::test_ncd_is_symmetric` | Planned |
| FR-4.6 | AC-M3-10 | `tests/test_algorithms/test_ncd.py::test_ncd_two_empty_strings_is_zero` | Planned |
| FR-3.5 | AC-M3-11 | `tests/test_algorithms/test_registry.py::test_list_algorithms_includes_levenshtein_and_ncd` | Planned |
| FR-3.5 | AC-M3-12 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_threshold_param_spec` | Planned |
| FR-4.7 | AC-M3-13 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_pairs_rows_within_threshold` | Planned |
| FR-4.7 | AC-M3-14 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_does_not_pair_rows_above_threshold` | Planned |
| FR-4.7 | AC-M3-15 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_threshold_zero_matches_only_identical` | Planned |
| FR-4.5, FR-4.7 | AC-M3-16 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_respects_block_boundaries` | Planned |
| FR-4.7 | AC-M3-17 | `tests/test_algorithms/test_levenshtein_nn.py::test_levenshtein_uses_rapidfuzz_score_cutoff` | Planned |
| FR-3.5 | AC-M3-18 | `tests/test_algorithms/test_registry.py::test_list_algorithms_includes_levenshtein_and_ncd` (same parametrized test covers both) | Planned |
| FR-3.5 | AC-M3-19 | `tests/test_algorithms/test_ncd_algorithm.py::test_ncd_algorithm_threshold_param_spec` | Planned |
| FR-4.6 | AC-M3-20 | `tests/test_algorithms/test_ncd_algorithm.py::test_ncd_algorithm_ui_threshold_scaled_internally` | Planned |
| FR-4.6 | AC-M3-21 | `tests/test_algorithms/test_ncd_algorithm.py::test_ncd_algorithm_pairs_rows_within_threshold` | Planned |
| FR-4.6 | AC-M3-22 | `tests/test_algorithms/test_ncd_algorithm.py::test_ncd_algorithm_does_not_pair_rows_above_threshold` | Planned |
| FR-4.5, FR-4.6 | AC-M3-23 | `tests/test_algorithms/test_ncd_algorithm.py::test_ncd_algorithm_respects_block_boundaries` | Planned |
| FR-4.4, FR-4.5 | AC-M3-24 | `tests/test_services/test_matching_service.py::test_run_matching_calls_extract_columns_for_nn_algorithm` | Planned |
| FR-4.4 | AC-M3-25 | `tests/test_services/test_matching_service.py::test_run_matching_passes_none_blocks_to_key_collision_algorithm` | Planned |
| FR-4.4 | AC-M3-26 | `tests/test_services/test_matching_service.py::test_union_find_merges_transitive_pairs_into_one_cluster` | Planned |
| FR-4.4 | AC-M3-27 | `tests/test_services/test_matching_service.py::test_candidate_pair_distance_is_max_pairwise_distance` | Planned |
| FR-4.4 | AC-M3-28 | `tests/test_services/test_matching_service.py::test_candidate_pairs_have_unique_pair_ids` | Planned |
| FR-4.1 | AC-M3-29 | `tests/test_services/test_matching_service.py::test_run_matching_rebuilds_candidate_pairs_from_scratch_nn_path` | Planned |
| FR-4.4 | AC-M3-30 | `tests/test_algorithms/test_base.py::test_candidate_pair_has_pair_id_field` | Planned |
| FR-3.5, FR-3.4 | AC-M3-31 | `tests/test_routers/test_algorithm.py::test_post_algorithm_levenshtein_threshold_zero_accepted` | Planned |
| FR-3.5, FR-3.4 | AC-M3-32 | `tests/test_routers/test_algorithm.py::test_post_algorithm_levenshtein_negative_threshold_rejected`, `::test_post_algorithm_levenshtein_non_integer_threshold_rejected` | Planned |
| FR-3.5, FR-3.4 | AC-M3-33 | `tests/test_routers/test_algorithm.py::test_post_algorithm_ncd_threshold_in_range_accepted` | Planned |
| FR-3.5, FR-3.4 | AC-M3-34 | `tests/test_routers/test_algorithm.py::test_post_algorithm_ncd_threshold_zero_rejected` | Planned |
| FR-3.5, FR-3.4 | AC-M3-35 | `tests/test_routers/test_algorithm.py::test_post_algorithm_ncd_threshold_above_10_rejected` | Planned |
| FR-3.5, FR-3.4 | AC-M3-36 | `tests/test_routers/test_algorithm.py::test_post_algorithm_fingerprint_ignores_threshold` | Planned |
| FR-3.5 | AC-M3-37 | `tests/test_routers/test_algorithm.py::test_get_algorithm_renders_threshold_input` | Planned |
| FR-5.1 | AC-M3-38 | `tests/test_routers/test_results.py::test_get_results_shows_edit_distance_sub_label_for_levenshtein` | Planned |
| FR-5.1 | AC-M3-39 | `tests/test_routers/test_results.py::test_get_results_shows_ncd_score_sub_label_for_ncd` | Planned |
| FR-5.1 | AC-M3-40 | `tests/test_routers/test_results.py::test_get_results_no_nn_sub_label_for_key_collision` | Planned |
| FR-4.3 | AC-M3-41 | `tests/test_algorithms/test_backend_agnosticism.py::test_algorithms_file_does_not_import_pandas` (parametrized to include `blocking.py`, `ncd.py`, `nearest_neighbor.py`) | Planned |

## M4-M5

Not yet authored — to be added by the BA pass that runs before each of
those milestones' `coder` passes start.
