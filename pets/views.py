from django.shortcuts import render
from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from .serializers import PetSerializer
from .models import Pet
from groups.models import Group
from traits.models import Trait
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        traits_params = request.query_params.get("trait")
        if traits_params:
            traits_id = Trait.objects.filter(name=traits_params).first()
            pets_trait = Pet.objects.filter(traits=traits_id).all()
            pages = self.paginate_queryset(pets_trait, request)
            serializar = PetSerializer(pages, many=True)
            return self.get_paginated_response(serializar.data)

        pets = Pet.objects.all()
        pages = self.paginate_queryset(pets, request)

        serializar = PetSerializer(pages, many=True)

        return self.get_paginated_response(serializar.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pet_group = serializer.validated_data.pop("group")
        pet_trait = serializer.validated_data.pop("traits")

        group_obj = Group.objects.filter(
            scientific_name__iexact=pet_group["scientific_name"]
        ).first()
        if not group_obj:
            group_obj = Group.objects.create(**pet_group)

        pet_obj = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait_dict in pet_trait:
            traits_obj = Trait.objects.filter(name__iexact=trait_dict["name"]).first()
            if not traits_obj:
                traits_obj = Trait.objects.create(**trait_dict)
            pet_obj.traits.add(traits_obj)

        serializer = PetSerializer(pet_obj)

        return Response(serializer.data, status.HTTP_201_CREATED)


class PetDetailView(APIView, PageNumberPagination):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        pet_group: dict = serializer.validated_data.pop("group", None)
        pet_trait: dict = serializer.validated_data.pop("traits", None)

        if pet_group:
            group_obj = Group.objects.filter(
                scientific_name__iexact=pet_group["scientific_name"]
            ).first()
            if not group_obj:
                group_obj = Group.objects.create(**pet_group)

            pet.group = group_obj
            pet.save()

        if pet_trait:
            pet.traits.clear()
            for trait_dict in pet_trait:
                print(trait_dict)
                traits_obj = Trait.objects.filter(
                    name__iexact=trait_dict["name"]
                ).first()
                if not traits_obj:
                    traits_obj = Trait.objects.create(**trait_dict)
                pet.traits.add(traits_obj)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()
        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
