"""Implementation example of a cell-centered Finite Volume Method for the
steadystate diffusion equation. The equation is of the form:

.. math::

  0 = \\nabla \\cdot \\big[ D(\\mathbf{r}) \\ \\nabla\\phi(\\mathbf{r}) \\big]

Where :math:`D(\\mathbf{r})` is the diffusion coefficient and
:math:`\\phi(\\mathbf{r})` is the density of the diffusion material.

"""

import numpy as np

from elliptic.Kernel.EntityKernelMixins import DimensionEntityKernelMixin
from elliptic.Kernel.ArrayKernelMixins import (FillVectorKernelMixin,
                                               FillMatrixKernelMixin)

from .Physical import Dirichlet


class EquivDiff(DimensionEntityKernelMixin, FillVectorKernelMixin):
    """Kernel which calculates the equivalent diffusivity in the faces.

    """
    entity_dim = 2
    bridge_dim = 2
    target_dim = 3
    depth = 1
    solution_dim = 2

    @classmethod
    def run(cls, m, elem):
        adj = cls.get_adj(m, elem, cls.bridge_dim, cls.target_dim, cls.depth)

        if len(adj) > 1:
            edge_center = cls.get_center(m, elem)
            el1_center = cls.get_center(m, adj[0])
            el2_center = cls.get_center(m, adj[1])
            dx1 = np.linalg.norm(el1_center - edge_center)
            dx2 = np.linalg.norm(el2_center - edge_center)
            D1 = cls.get_physical(m, adj[0]).value
            D2 = cls.get_physical(m, adj[1]).value

            D_equiv = (2*D1*D2) / (D1*dx2 + D2*dx1)

            cls.fill_array(m, [(elem, D_equiv)])
        else:
            cls.fill_array(m, [(elem, 0)])


class FillDiag(DimensionEntityKernelMixin, FillMatrixKernelMixin):
    """Fills the matrix diagonals.

    """
    array_name = "A"
    share = True

    entity_dim = 3
    solution_dim = 3

    @classmethod
    def run(cls, m, elem):
        # Default value
        value = 0

        for dim in range(0, cls.entity_dim):
            adj_faces_physical = cls.get_adj_physical(
                m, elem, dim, dim, phys_type=Dirichlet)
            # If the current element has a boundary condition,
            # sets value to 1
            if adj_faces_physical:
                    value = 1
                    break

        results = {
            'set': [(elem, [elem], [value])],
            'sum': []
        }

        cls.fill_array(m, results)


class FillBoundary(DimensionEntityKernelMixin, FillVectorKernelMixin):
    """Fills the vector 'b' with boundary conditions.

    """
    array_name = "b"
    entity_dim = 3
    solution_dim = 3

    @classmethod
    def run(cls, m, elem):
        value = 0

        for dim in range(0, cls.entity_dim):
            adj_faces_physical = cls.get_adj_physical(
                m, elem, dim, dim, phys_type=Dirichlet)
            # If the current element has a boundary condition,
            # sets value to 1
            if adj_faces_physical:
                    value = adj_faces_physical.value
                    break

        cls.fill_array(m, [(elem, value)])


class CCFVMKernel(DimensionEntityKernelMixin, FillMatrixKernelMixin):
    """Example kernel for the CC-FVM method. This kernel iterates on the mesh
    faces and fills the transmissibility matrix accordingly.

    """
    array_name = "A"
    share = True

    entity_dim = 2
    bridge_dim = 2
    target_dim = 3
    depth = 1
    solution_dim = 3

    depends = [EquivDiff, FillDiag, FillBoundary]

    @classmethod
    def run(cls, m, elem):
        results = {
            'set': [],
            'sum': []
        }

        # Gets the equivalent diffusivity for the face
        K_equiv = cls.EquivDiff_array[elem]

        adj = cls.get_adj(m, elem, cls.bridge_dim, cls.target_dim, cls.depth)
        adj = list(adj)

        # If the face has two adjacend volumes
        if len(adj) == 2:
            # Check if those volumes do not have any faces with boundary
            # conditions of type Dirichlet
            for dim in range(0, cls.entity_dim):
                adj0_faces_physical = cls.get_adj_physical(
                    m, adj[0], dim, dim, phys_type=Dirichlet)
                # Uses the first Dirichlet condition found
                if adj0_faces_physical:
                        break

            for dim in range(0, cls.entity_dim):
                adj1_faces_physical = cls.get_adj_physical(
                    m, adj[1], dim, dim, phys_type=Dirichlet)
                # Uses the first Dirichlet condition found
                if adj1_faces_physical:
                        break

            if not adj0_faces_physical:
                results['set'].append((adj[0], [adj[1]], [-K_equiv]))
                results['sum'].append((adj[0], [adj[0]], [K_equiv]))

            if not adj1_faces_physical:
                results['set'].append((adj[1], [adj[0]], [-K_equiv]))
                results['sum'].append((adj[1], [adj[1]], [K_equiv]))

        cls.fill_array(m, results)
