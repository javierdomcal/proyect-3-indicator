%chk=649210.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

649210 hydrogen_2eq CASSCF(2,2) TZVP

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

649210.wfx

