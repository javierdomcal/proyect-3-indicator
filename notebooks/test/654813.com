%chk=654813.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

654813 hydrogen CASSCF(2,2) TZVP

0 1
H    0.000000   0.000000  -0.370000
H    0.000000   0.000000   0.370000

654813.wfx

