# Example Markdown

```ruby
require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html
```

| Tables   |      Are      |  Cool |
|----------|:-------------:|------:|
| col 1 is |  left-aligned | $1600 |
| col 2 is |    centered   |   $12 |
| col 3 is | right-aligned |    $1 |

> The first rule about fight club is you don’t talk about fight club.
>
> The second rule about fight club is you don’t talk about fight club.


```json
{
  "firstName": "John",
  "lastName": "Smith",
  "age": 25
}
```