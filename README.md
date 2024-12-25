# SS14 YAML Sanitizer

A tool quickly clean up Space Station 14 entity prototypes.

## What is this?

This tool analyzes your entity prototypes and removes redundant components and fields that are already inherited from parent entities. It helps maintain cleaner, more manageable prototype files by:

- Removing completely duplicate components that exist in parent entities
- Stripping out redundant field values that match parent components
- Preserving only the unique overrides your entity actually needs
- Maintaining proper field ordering

In other words: It stops you from copy-pasting entire components when you only needed to change one field.

## What this won't do

This isn't magic. It won't:

- Fix poorly designed inheritance hierarchies
- Make bad component composition decisions good
- Write your prototypes for you
- Make you a better YAML warrior
- Fix prototype logic errors

## Setup

1. Clone this repository
2. Install the dependencies:
```bash
pip install ruamel.yaml tqdm
```

## Usage

Run the sanitizer with:

```bash
python yaml_sanitizer.py --dir /path/to/your/Resources --id EntityPrototypeId --output sanitized.yml
```

Where:
- `--dir`: The **absolute** path to your SS14 Resources directory containing entity prototypes
- `--id`: The ID of the prototype you want to sanitize
- `--output`: Where to save the sanitized prototype (defaults to output.yml)

## Example

Here's a real example - a telegnostic projection prototype before sanitization:

```yaml
- type: entity
  parent: [ Incorporeal, BaseMob ]
  id: MobObserverTelegnostic
  name: telegnostic projection
  description: Ominous.
  categories: [ HideSpawnMenu ]
  components:
  - type: Sprite
    overrideContainerOcclusion: true
    noRot: true
    drawdepth: Ghosts
    sprite: Objects/Consumable/Food/bowl.rsi
    state: eyeball
    color: "#90EE90"
    layers:
      - state: eyeball
        shader: unshaded
  - type: Psionic
  - type: MindContainer
  - type: Clickable
  - type: InteractionOutline
  - type: Physics
    bodyType: KinematicController
    fixedRotation: true
  - type: Fixtures
    fixtures:
      fix1:
        shape:
          !type:PhysShapeCircle
          radius: 0.35
        density: 13
        mask:
        - GhostImpassable
  - type: MovementSpeedModifier
    baseSprintSpeed: 8
    baseWalkSpeed: 5
  - type: MovementIgnoreGravity
  - type: InputMover
  - type: Appearance
  - type: Eye
    drawFov: false
    visMask:
      - Normal
      - TelegnosticProjection
  - type: Input
    context: "ghost"
  - type: Examiner
  - type: TelegnosticProjection
  - type: Stealth
    lastVisibility: 0.66
  - type: Visibility
    layer: 4
  - type: NoNormalInteraction
```

After sanitization (removing components inherited from Incorporeal and BaseMob):

```yaml
- type: entity
  parent: [ Incorporeal, BaseMob ]
  id: MobObserverTelegnostic
  categories: [ HideSpawnMenu ]
  name: telegnostic projection
  description: Ominous.
  components:
  - type: Sprite
    sprite: Objects/Consumable/Food/bowl.rsi
    state: eyeball
    color: "#90EE90"
    layers:
      - state: eyeball
        shader: unshaded
  - type: Psionic
  - type: Physics
    fixedRotation: true
  - type: Fixtures
    fixtures:
      fix1:
        shape:
          !type:PhysShapeCircle
          radius: 0.35
        density: 13
        mask:
        - GhostImpassable
  - type: MovementSpeedModifier
    baseSprintSpeed: 8
    baseWalkSpeed: 5
  - type: Eye
    drawFov: false
    visMask:
      - Normal
      - TelegnosticProjection
  - type: Input
    context: "ghost"
  - type: TelegnosticProjection
  - type: Stealth
    lastVisibility: 0.66
  - type: Visibility
    layer: 4
  - type: NoNormalInteraction
```

Notice how components like `MindContainer`, `Clickable`, `InteractionOutline`, etc. were removed since they're inherited from parent entities. The tool also removed redundant fields from components while preserving only the overridden values.

## Contributing

PRs welcome! Please make sure to test your changes against a variety of entity prototypes before submitting.

## License

MIT License - See LICENSE file for details

## Credits

Made with ❤️ (and frustration) by MilonPL