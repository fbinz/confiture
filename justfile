manage *options:
  #!/usr/bin/env bash
  cd src
  python ./manage.py {{options}}


tailwind:
  #!/usr/bin/env bash
  cd src/static_src
  mkdir ../static/css -p
  npx tailwindcss -i ./css/input.css -o ../static/css/output.css --watch
