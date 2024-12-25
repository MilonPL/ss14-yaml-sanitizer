#!/usr/bin/env python3
"""
Space Station 14 YAML Sanitizer
This script removes redundant components from entity prototypes that are already inherited from parent entities.
"""

from pathlib import Path
from ruamel.yaml import YAML
from tqdm import tqdm
from typing import Dict, List, Any, Optional
import argparse
import copy
import time

class YAMLSanitizer:
    # Define the correct order of fields for entity prototypes
    PROTOTYPE_FIELD_ORDER = [
        'type',
        'abstract',
        'parent',
        'id',
        'categories',
        'name',
        'suffix',
        'description',
        'components'
    ]

    def __init__(self):
        self.yaml = YAML(typ='rt')
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
        self.yaml.indent(mapping=2, sequence=2, offset=0)
        self.yaml.default_flow_style = False
        self.yaml.allow_unicode = True
        self.yaml.explicit_start = False
        self.yaml.explicit_end = False
        self.yaml.sequence_dash_offset = 0
        self.prototypes: Dict[str, Any] = {}

    def _order_prototype_fields(self, prototype: Dict[str, Any]) -> Dict:
        """Reorder prototype fields."""
        ordered = {}

        # First add fields in the correct order if they exist
        for field in self.PROTOTYPE_FIELD_ORDER:
            if field in prototype:
                ordered[field] = prototype[field]

        # Then add any remaining fields that weren't in our ordered list
        for key, value in prototype.items():
            if key not in ordered:
                ordered[key] = value

        return ordered

    def load_all_prototypes(self, base_dir: Path) -> None:
        """Recursively load all entity prototypes from YAML files in the directory structure."""
        print("Scanning directory for YAML files...")
        start_time = time.time()

        yaml_files = list(base_dir.rglob('*.yml'))
        total_files = len(yaml_files)
        print(f"Found {total_files} YAML files")

        loaded_count = 0
        error_count = 0

        with tqdm(total=total_files, desc="Loading prototypes") as pbar:
            for yaml_file in yaml_files:
                try:
                    try:
                        with open(yaml_file, 'r', encoding='utf-8-sig') as f:
                            content = f.read()
                    except UnicodeError:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                    data = self.yaml.load(content)
                    if not isinstance(data, list):
                        pbar.update(1)
                        continue

                    file_count = 0
                    for prototype in data:
                        if not isinstance(prototype, dict) or \
                                prototype.get('type') != 'entity' or \
                                'id' not in prototype:
                            continue

                        self.prototypes[prototype['id']] = prototype
                        loaded_count += 1
                        file_count += 1

                    if file_count > 0:
                        tqdm.write(f"Loaded {file_count} prototypes from {yaml_file.name}")
                    pbar.set_postfix({'prototypes': loaded_count}, refresh=True)

                except Exception as e:
                    error_count += 1
                    tqdm.write(f"Error loading {yaml_file}: {e}")

                pbar.update(1)

        elapsed_time = time.time() - start_time
        print(f"\nLoading complete in {elapsed_time:.2f} seconds:")
        print(f"- Processed {total_files} YAML files")
        print(f"- Loaded {loaded_count} entity prototypes")
        if error_count > 0:
            print(f"- Encountered {error_count} errors")

    @staticmethod
    def get_component_from_parent(parent: Dict[str, Any], comp_type: str) -> Optional[Dict[str, Any]]:
        """Get a component configuration from a parent prototype."""
        if 'components' not in parent:
            return None

        for comp in parent['components']:
            if isinstance(comp, dict) and comp.get('type') == comp_type:
                return comp
        return None

    def are_components_equal(self, comp1: Dict[str, Any], comp2: Dict[str, Any]) -> bool:
        """Compare two components for equality."""
        # Ignore type field in comparison
        comp1_data = {k: v for k, v in comp1.items() if k != 'type'}
        comp2_data = {k: v for k, v in comp2.items() if k != 'type'}

        # If both components have only type field, they are equal
        if not comp1_data and not comp2_data:
            return True

        # If one has data and the other doesn't, they're not equal
        if bool(comp1_data) != bool(comp2_data):
            return False

        try:
            return self._compare_values(comp1_data, comp2_data)
        except Exception:
            return False

    def _compare_values(self, val1: Any, val2: Any) -> bool:
        """Recursively compare two values."""
        if type(val1) != type(val2):
            return False

        if isinstance(val1, dict):
            return all(k in val2 and self._compare_values(v, val2[k]) for k, v in val1.items())

        if isinstance(val1, list):
            if len(val1) != len(val2):
                return False
            return all(self._compare_values(v1, v2) for v1, v2 in zip(val1, val2))

        if hasattr(val1, 'value') and hasattr(val2, 'value'):
            return val1.value == val2.value

        return val1 == val2

    def _remove_redundant_fields(self, component: Dict[str, Any], parents_components: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """Remove fields from component that are identical to any parent's fields."""
        result = component.copy()
        redundant_fields = set()

        for parent_comp in parents_components:
            for key, value in component.items():
                if key == 'type':
                    continue

                # If this field exists in any parent with the same value, mark it as redundant
                if key in parent_comp and self._compare_values(value, parent_comp[key]):
                    redundant_fields.add(key)

        # Remove all redundant fields
        for field in redundant_fields:
            if field in result:
                del result[field]

        if redundant_fields:
            print(f"- Removed redundant fields: {redundant_fields}")

        return result

    def get_all_parent_components(self, prototype: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Get all components from the prototype's parent chain."""
        parent_components: Dict[str, List[Dict[str, Any]]] = {}

        parents = prototype.get('parent', [])
        if isinstance(parents, str):
            parents = [parents]
        elif not isinstance(parents, list):
            return parent_components

        for parent_id in parents:
            if parent_id not in self.prototypes:
                print(f"Warning: Parent prototype '{parent_id}' not found")
                continue

            parent = self.prototypes[parent_id]

            # Get parent's components
            if 'components' in parent:
                for comp in parent['components']:
                    if isinstance(comp, dict) and 'type' in comp:
                        comp_type = comp['type']
                        if comp_type not in parent_components:
                            parent_components[comp_type] = []
                        parent_components[comp_type].append(comp)

            # Recursively get components from parent's parents
            parent_comps = self.get_all_parent_components(parent)
            for comp_type, configs in parent_comps.items():
                if comp_type not in parent_components:
                    parent_components[comp_type] = []
                parent_components[comp_type].extend(configs)

        return parent_components

    def sanitize_prototype(self, prototype: Dict[str, Any]) -> Dict[str, Any]:
        """Remove redundant components and fields that are already inherited from parents."""
        sanitized = copy.deepcopy(prototype)

        if 'components' not in sanitized or not isinstance(sanitized['components'], list):
            return self._order_prototype_fields(sanitized)

        parent_components = self.get_all_parent_components(sanitized)
        components_to_remove = []

        for i, component in enumerate(sanitized['components']):
            if not isinstance(component, dict) or 'type' not in component:
                continue

            comp_type = component['type']

            if comp_type in parent_components:
                parent_comps = parent_components[comp_type]

                # First check if component is completely redundant
                for parent_comp in parent_comps:
                    if self.are_components_equal(component, parent_comp):
                        components_to_remove.append((i, comp_type))
                        break
                else:
                    # If component is not completely redundant, try to remove redundant fields
                    cleaned_comp = self._remove_redundant_fields(component, parent_comps)
                    if cleaned_comp != component:
                        sanitized['components'][i] = cleaned_comp

        # Remove redundant components
        if components_to_remove:
            print(f"\nRemoving {len(components_to_remove)} redundant components")
            for i, comp_type in reversed(components_to_remove):
                del sanitized['components'][i]
                print(f"- {comp_type}")
        else:
            print("\nNo redundant components found")

        # Order the fields before returning
        return self._order_prototype_fields(sanitized)

    def find_and_sanitize_prototype(self, prototype_id: str, output_file: str) -> bool:
        """Find a specific prototype by ID, sanitize it, and save to output file."""
        if prototype_id not in self.prototypes:
            print(f"Error: Prototype '{prototype_id}' not found")
            return False

        print(f"\nFound prototype '{prototype_id}'\n")

        original = self.prototypes[prototype_id]
        sanitized = self.sanitize_prototype(original)

        output_path = Path(output_file)
        print(f"\nSaving sanitized prototype to {output_path}")

        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            self.yaml.dump([sanitized], f)

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Sanitize a specific Space Station 14 entity prototype'
    )
    parser.add_argument(
        '--dir',
        type=str,
        required=True,
        help='base directory containing entity prototype YAML files'
    )
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='ID of the prototype to sanitize'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output.yml',
        help='output file path (default: output.yml)'
    )

    args = parser.parse_args()

    try:
        print("\nSS14 YAML Sanitizer")
        print("Made by MilonPL")
        print("==============================\n")

        sanitizer = YAMLSanitizer()
        sanitizer.load_all_prototypes(Path(args.dir))
        if sanitizer.find_and_sanitize_prototype(args.id, args.output):
            print("\nDone!")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()