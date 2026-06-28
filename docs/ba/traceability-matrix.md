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
| FR-2.4, FR-2.6 | AC-M1-11 | `tests/test_routers/test_mapping.py::test_post_mapping_valid_redirects` | Done |
| FR-2.5 | AC-M1-12 | `tests/test_routers/test_mapping.py::test_post_mapping_street_col_not_a_real_header_returns_422` | Done |
| FR-2.5 | AC-M1-13 | `tests/test_routers/test_mapping.py::test_post_mapping_zip_col_not_a_real_header_returns_422` | Done |
| FR-2.4 | AC-M1-14 | `tests/test_routers/test_mapping.py::test_post_mapping_without_zip_or_city_returns_422` | Done |
| FR-2.3 | AC-M1-15 | `tests/test_routers/test_mapping.py::test_post_mapping_then_get_shows_chosen_mapping_not_best_guess` | Done |
| FR-6.1 (stub) | (M1 stub behavior) | `tests/test_compute/test_pandas_backend.py::test_replace_values_raises_not_implemented` | Done |

## M2 — Fingerprint + N-Gram Fingerprint Algorithms + Read-Only Results (planned)

| Requirement | Acceptance Criteria | Test file/case | Status |
|---|---|---|---|
| FR-3.1 | AC-M2-1 | `tests/test_algorithms/test_base.py::test_matching_algorithm_abc_shape` | Planned |
| FR-4.3 | AC-M2-2 | `tests/test_algorithms/test_base.py::test_algorithm_output_carries_clusters_for_key_collision` | Planned |
| FR-3.1, FR-3.3 | AC-M2-3 | `tests/test_algorithms/test_registry.py::test_list_algorithms_includes_fingerprint_and_ngram` | Planned |
| FR-4.2 | AC-M2-4 | `tests/test_algorithms/test_fingerprint.py::test_normalization_case_and_punctuation_insensitive` | Planned |
| FR-4.2 | AC-M2-5 | `tests/test_algorithms/test_fingerprint.py::test_normalization_collapses_whitespace` | Planned |
| FR-4.2 | AC-M2-6 | `tests/test_algorithms/test_fingerprint.py::test_token_order_does_not_affect_key` | Planned |
| FR-4.2 | AC-M2-7 | `tests/test_algorithms/test_fingerprint.py::test_duplicate_tokens_deduplicated` | Planned |
| FR-4.2 | AC-M2-8 | `tests/test_algorithms/test_fingerprint.py::test_non_matching_addresses_not_clustered` | Planned |
| FR-4.2 | AC-M2-9 | `tests/test_algorithms/test_fingerprint.py::test_blank_address_excluded_from_clustering` | Planned |
| FR-4.2 | AC-M2-10 | `tests/test_services/test_matching_service.py::test_singleton_keys_produce_no_candidate_pair` | Planned |
| FR-3.3 | AC-M2-11 | `tests/test_algorithms/test_ngram_fingerprint.py::test_default_n_is_2` | Planned |
| FR-4.2 | AC-M2-12 | `tests/test_algorithms/test_ngram_fingerprint.py::test_ngram_key_construction_uses_hyphen_delimiter` | Planned |
| FR-4.2 | AC-M2-13 | `tests/test_algorithms/test_ngram_fingerprint.py::test_strings_shorter_than_n_excluded` | Planned |
| FR-3.4 | AC-M2-14 | `tests/test_algorithms/test_ngram_fingerprint.py::test_different_n_can_change_clusters` | Planned |
| FR-4.1 | AC-M2-15 | `tests/test_services/test_matching_service.py::test_run_matching_uses_extract_street_addresses` | Planned |
| FR-4.1 | AC-M2-16 | `tests/test_services/test_matching_service.py::test_run_matching_rebuilds_candidate_pairs` | Planned |
| FR-4.2 | AC-M2-17 | `tests/test_services/test_matching_service.py::test_cluster_becomes_one_candidate_pair_entry` | Planned |
| FR-3.2 | AC-M2-18 | `tests/test_routers/test_algorithm.py::test_get_algorithm_lists_fingerprint_and_ngram` | Planned |
| FR-3.2 | AC-M2-19 | `tests/test_routers/test_algorithm.py::test_get_algorithm_without_mapping_redirects` | Planned |
| FR-3.4 | AC-M2-20 | `tests/test_routers/test_algorithm.py::test_post_algorithm_persists_and_runs_matching` | Planned |
| FR-5.1 | AC-M2-21 | `tests/test_routers/test_results.py::test_get_results_renders_groups_readonly` | Planned |
| FR-5.1 | AC-M2-21a | `tests/test_routers/test_results.py::test_get_results_distance_column_blank_for_key_collision` | Planned |
| FR-5.1 | AC-M2-22 | `tests/test_routers/test_results.py::test_get_results_without_algorithm_redirects` | Planned |
| FR-4.3 | AC-M2-23 | reviewer pass (static check: no `import pandas` under `app/algorithms/`) | Planned |
| FR-2.6 (updated) | AC-M2-24 | `tests/test_routers/test_mapping.py::test_post_mapping_valid_redirects_to_algorithm` | Planned |
| FR-3.4 | AC-M2-25 | `tests/test_routers/test_algorithm.py::test_post_algorithm_invalid_n_returns_422` | Planned |
| FR-5.1 | AC-M2-26 | `tests/test_routers/test_results.py::test_get_results_empty_state_suggests_next_action` | Planned |

## M3-M5

Not yet authored — to be added by the BA pass that runs before each of
those milestones' `coder` passes start.
