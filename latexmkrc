$pdf_mode = 1;
$out_dir  = 'build';
$bibtex_use = 2;

add_cus_dep('glo', 'gls', 0, 'makeglossaries');
sub makeglossaries {
  my ($base_name) = @_;
  return system("makeglossaries \"$base_name\"");
}
