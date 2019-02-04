from pathlib import Path

from scss import Compiler

from gilbert.content import Content


class SCSS(Content):

    def get_output_name(self):
        return Path(self.name).with_suffix('.css')

    def render(self, site):
        compiler_args = self.data.get('scss_options', {})
        compiler = Compiler(**compiler_args)

        with (site.dest_dir / self.get_output_name()).open('w') as fout:
            fout.write(compiler.compile_string(self.content))
