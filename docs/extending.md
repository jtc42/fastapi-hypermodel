# Extending

It is possible to define new custom hypermedia formats. There are three aspects
to consider:

- Skeleton Type: this is a class to for the underlying representation of the
  fields in the response, it could be a single class (`URLForType`,
  `HALForType`) or mutiple classes (`SirenActionType`, `SirenEmbeddedType`,
  `SirenFieldType`, `SirenLinkType`). This skeleton type has the `Type` suffix
  as a convention but it is not required.
- Builder Type: this is a helper class that inspects the app and gathers all the
  necessary information to build the skeleton type. It it recommended to make it
  a subclass of the skeleton type and also inherit from
  `AbstractHyperField[SkeletonType]`. Some examples are `URLFor` and `HALFor`
- Hypermodel Type: This is an optional class to include response-wide logic.
  `URLFor` has no Hypermodel type and leverages the base one, whereas HAL
  implements `HALHyperModel` and uses it to handle the cURIes logic. Siren uses
  the `SirenHyperModel` to move the different fields into `properties` and
  `entitites`. This is usually required for Level 1+ Hypermedia formats
- Response Type: This is an optional class to define custom response behaviour.
  It could be lightweight like `SirenResponse` where only a jsonchema is
  checked, or it could be more complex like `HALReponse`. If no custom
  content-type is needed, it could be omitted, as it happens with `URLFor`.

All the formats (URLFor, HAL and Siren) are implemented in the same way a custom
type could be implemented. 

