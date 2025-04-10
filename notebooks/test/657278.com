%chk=657278.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(4,5)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

657278 beryllium_atom CASSCF(4,5) cc-pVDZ

0 1
Be    0.0000   0.0000   0.0000

657278.wfx

