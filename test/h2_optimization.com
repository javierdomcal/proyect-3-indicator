%chk=h2_optimization.chk
%mem=4GB
%NProcShared=4
#P Opt CISD/6-31G(d) gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

h2_optimization hydrogen CISD 6-31G(d)

0 1
H    0.0000   0.0000   0.0000
H    0.7400   0.0000   0.0000

h2_optimization.wfx
